# EEG_preproc/src/pipeline_main.py

from pathlib import Path
import pandas as pd
from .io_raw import load_raw_brainvision_bids
from .sleep_annotations import attach_sleep_annotations
from .filtering import filter_and_resample
from .epoching import (
    create_sleep_epochs,
    create_fixed_length_epochs,
    segment_sleep_annotations_to_events,
    check_epoch_groups,
)

from .session_segmentation import split_raw_by_bids_events, save_phase_raws
from .cleaning import run_nice_cleaning, save_preica_raws

from .qc_epoching import (
    compute_epoch_qc,
    save_subject_qc,
    plot_hypnogram,
)

from .qc_report import (
    add_channel_variance,
    init_report,
    add_raw_overview,
    add_psd_section,
    add_filter_comparison,
    add_segment_summary,
    add_nap_stage_distribution,
    add_hypnogram_to_report,
    add_bad_epoch_matrix,
    add_bad_channel_topomap,
    add_channel_variance,
    save_report,
)

from .summary_outputs import update_master_results, log_failed_subject


def run_preproc_subject(
    subject_id: str,
    paths: dict,
    pipeline_cfg: dict,
) -> None:

    bids_root   = paths["bids_root"]
    deriv_root  = paths["deriv_root"]
    report_root = paths["report_root"]
    logs_root   = paths["logs_root"]
    errors_root = paths["errors_root"]

    pipe_name = pipeline_cfg["name"]

    out_dir    = deriv_root  / pipe_name / f"sub-{subject_id}"
    report_dir = report_root / pipe_name / f"sub-{subject_id}"
    logs_dir   = logs_root   / pipe_name
    errors_dir = errors_root / pipe_name

    for p in [out_dir, report_dir, logs_dir, errors_dir]:
        p.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1) Load raw + initialize report
    # ---------------------------------------------------------


    report, report_file = init_report(
        subject_id,
        report_root / pipe_name
    )
    try: 
        raw = load_raw_brainvision_bids(
            subject=subject_id,
            session="01",
            bids_root=bids_root
        )

        add_raw_overview(report, raw)

        # ---------------------------------------------------------
        # 2) Filtering
        # ---------------------------------------------------------

        raw_before = raw.copy()

        raw = filter_and_resample(
            raw,
            pipeline_cfg["filter"]
        )

        add_filter_comparison(
            report,
            raw_before,
            raw,
            filter_cfg=pipeline_cfg["filter"]
        )

        # ---------------------------------------------------------
        # 3) Segment raw into experimental phases
        # ---------------------------------------------------------

        events_tsv = (
            bids_root
            / f"sub-{subject_id}"
            / "ses-01" #later, can loop through sessions if needed
            / "eeg"
            / f"sub-{subject_id}_ses-01_task-sleep_events.tsv"
        )

        phases = split_raw_by_bids_events(raw, events_tsv)

        raw_wake1  = phases["Wake1"]
        raw_nap    = phases["Nap"]
        raw_wake2  = phases["Wake2"]
        raw_passive = phases["Passive"]

        add_segment_summary(report, phases)

        for segment_name, raw_segment in phases.items():
            add_psd_section(report, raw_segment, segment_name)

        # ---------------------------------------------------------
        # 4) Epoching
        # ---------------------------------------------------------

        epoch_cfg = pipeline_cfg["epoching"]
        segment_length = epoch_cfg["segment_length"]

        # Wake phases → fixed epochs

        epochs_wake1 = create_fixed_length_epochs(
            raw_wake1,
            segment_length
        )

        epochs_wake2 = create_fixed_length_epochs(
            raw_wake2,
            segment_length
        )

        epochs_passive = create_fixed_length_epochs(
            raw_passive,
            segment_length
        )

        # Nap → annotation-based epochs

        raw_nap = attach_sleep_annotations(
            raw_nap,
            subject_id,
            paths,
            epoch_len=30,
            tolerance=5
        )

        allowed = {"W", "N1", "N2", "N3", "R"}

        labels = set(raw_nap.annotations.description)
    
        if not labels.issubset(allowed):

            unexpected = labels - allowed
            print(f"[WARNING] Unexpected sleep labels: {unexpected}")

        print("First 5 stage annotations:")
        for o, d, desc in zip(raw_nap.annotations.onset[:5],
                                raw_nap.annotations.duration[:5],
                                raw_nap.annotations.description[:5]):
                print(o, d, desc)
        # ann = raw_nap.annotations

        # mask = [desc in allowed for desc in ann.description]
        # stage_ann = ann[mask]
        # raw_nap.set_annotations(stage_ann)

        add_nap_stage_distribution(report, raw_nap)

        events, event_id = segment_sleep_annotations_to_events(
            raw_nap,
            raw_nap.annotations,
            segment_length=segment_length,
            group_map=epoch_cfg["group_map"],
        )

        epochs_nap = create_sleep_epochs(
            raw_nap,
            events,
            event_id,
            segment_length=segment_length,
        )

        check_epoch_groups(epochs_nap)

        save_phase_raws(
            phases,
            subject=subject_id,
            deriv_root=paths["deriv_root"],
            pipeline_name=pipeline_cfg["name"]
        )
        
        # ---------------------------------------------------------
        # 5) Collect epochs
        # ---------------------------------------------------------

        epochs_all = {
            "Wake1": epochs_wake1,
            "Nap": epochs_nap,
            "Wake2": epochs_wake2,
            "Passive": epochs_passive,
        }

        # ---------------------------------------------------------
        # 6) Structural QC
        # ---------------------------------------------------------

        qc_row = compute_epoch_qc(
            subject_id,
            phases,
            epochs_all,
            raw_nap
        )

        save_subject_qc(
            qc_row,
            subject_id,
            report_root / pipe_name
        )

        fig = plot_hypnogram(
            subject_id,
            raw_nap,
            report_root / pipe_name
        )

        add_hypnogram_to_report(
            report,
            fig
        )

    # ---------------------------------------------------------
    # 7) NICE CLEANING - BAD CHANNEL AND BAD EPOCH DETECTION
    # ---------------------------------------------------------

        sessions = {
            "wake1": raw_wake1,
            "nap": raw_nap,
            "wake2": raw_wake2,
            "passive": raw_passive
        }
        # function for saving the raw files

        #qc metrics for each session, including bad channel and bad epoch counts, to be added to the report and master summary
    
        for session_type, raw_session in epochs_all.items():

            epochs_session = epochs_all[session_type]

            #returns bad_channels and bad_epochs marked in the raw file, re-referenced and a dictionary of qc metrics
            raw_clean, qc_metrics = run_nice_cleaning(
                raw_session,
                epochs_session,
                session_type,
                pipeline_cfg,
                subject_id
            )

            # -----------------------------------------------------
            # Save RAW_preICA to derivatives
            # -----------------------------------------------------

            save_preica_raws(
                sessions,
                subject_id,
                deriv_root,
                pipeline_name=pipeline_cfg["name"]
            )

            print(
                f"{subject_id} | {session_type} | "
                f"{qc_metrics['bad_channel_count']} bad chans | "
                f"{qc_metrics['bad_epoch_count']} bad epochs"
            )
            add_bad_epoch_matrix(
                report,
                epochs_session,
                qc_metrics["bad_epochs"],
                subject_id,
                session_type
            )
            add_bad_channel_topomap(
                report,
                raw_clean,
                qc_metrics["bad_channels"],
                session_type
            )

            add_channel_variance(
                report,
                raw_clean,
                session_type
            )

            # -----------------------------------------------------
            # Save QC metrics
            # -----------------------------------------------------

            qc_file = Path(paths["logs_root"]) / "nice_cleaning_metrics.csv"
            qc_row = {
                "subject": subject_id,
                "session": session_type,
                "bad_channel_count": qc_metrics["bad_channel_count"],
                "bad_epoch_count": qc_metrics["bad_epoch_count"],
                "epochs_before": qc_metrics["epochs_before"],
                "epochs_after": qc_metrics["epochs_after"],
                "bad_channels": ",".join(qc_metrics["bad_channels"]),
            }
            df_row = pd.DataFrame([qc_row])

            # append or create
            if qc_file.exists():
                df_row.to_csv(qc_file, mode="a", header=False, index=False)
            else:
                df_row.to_csv(qc_file, index=False)

        
        
        
    # ---------------------------------------------------------
    # 8) ICA CLEANING - ON WAKE EPOCHS ONLY 
    # ---------------------------------------------------------

        # ---------------------------------------------------------
        # 9) Save QC report
        # ---------------------------------------------------------

        save_report(
            report,
            report_file
        )

        # ---------------------------------------------------------
        # 8) Update master summary
        # ---------------------------------------------------------

        cleaning_info = None

        update_master_results(
            subject_id,
            pipe_name,
            cleaning_info,
            logs_dir,
        )
    except Exception as e:

        log_failed_subject(
            subject_id,
            pipe_name,
            error_stage="pipeline",
            error_message=e,
            errors_dir=errors_dir
        )

        raise e
