# EEG_preproc/src/pipeline_main.py
from pathlib import Path


from EEG_preproc.src.epoching import segment_sleep_annotations_to_events
from .io_raw import load_raw_brainvision_bids
from .sleep_annotations import attach_sleep_annotations
from .filtering import filter_and_resample
from .epoching import create_sleep_epochs, segment_sleep_annotations_to_events, create_fixed_length_epochs, check_epoch_groups
# from .cleaning import run_nice_cleaning_by_group
# from .bad_marking import apply_bad_channels_and_epochs
from src.qc_epoching import (
    compute_epoch_qc,
    save_subject_qc,
    plot_hypnogram,
)
from .qc_report import add_phase_summary, init_report, save_report, add_psd_section, add_filter_comparison, add_hypnogram_to_report, add_epoch_summary
from .summary_outputs import update_master_results
from .qc_report import (
    init_report,
    add_raw_overview,
    add_psd_section,
    add_filter_comparison,
    save_report
)

from .session_segmentation import split_raw_by_bids_events

# main pipeline function to run for each subject
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

    out_dir      = deriv_root  / pipe_name / f"sub-{subject_id}"
    report_dir   = report_root / pipe_name
    logs_dir     = logs_root   / pipe_name
    errors_dir   = errors_root / pipe_name

    for p in [out_dir, report_dir, logs_dir, errors_dir]:
        p.mkdir(parents=True, exist_ok=True)

    # 1) Load & set channel types
    #initiate MNE report and load raw data
    report, report_file = init_report(
        subject,
        paths["report_root"]
    )
    raw = load_raw_brainvision_bids(
        subject=subject,
        session="01", 
        bids_root=paths["bids_root"]
    )
    raw = set_channel_types(raw)
    add_raw_overview(report, raw)

    # 2) Filter
    #filter and downsample raw object first
    raw_before = raw.copy()
    raw = filter_and_resample(raw, config["filter"])
    #report for filtering comparison
    add_filter_comparison(report, raw_before, raw)

    # 3) Segment raw into phases (Wake1, Nap, Wake2, Passive) using BIDS events.tsv
    # Load the BIDS events TSV to get the time points for different phases (Wake1, Nap, Wake2, Passive)
    events_tsv = (
        paths["bids_root"]
        / f"sub-{subject}"
        / "ses-01"
        / "eeg"
        / f"sub-{subject}_ses-01_task-sleep_events.tsv"
    )

    phases = split_raw_by_bids_events(raw, events_tsv)

    raw_wake1 = phases["Wake1"]
    raw_nap = phases["Nap"]
    raw_wake2 = phases["Wake2"]
    raw_passive = phases["Passive"]

    # save derivatives
    save_phase_raws(
        phases,
        subject=subject,
        deriv_root=paths["deriv_root"]
    )
    #compute QC metrics for epochs and sleep stages, and save to CSV
    add_phase_summary(report, phases)
    
    #add PSD section to report for each phase
    for phase_name, raw_phase in phases.items():
        add_psd_section(report, raw_phase, title=f"{phase_name} - PSD")

    # 4) Attach sleep annotations (Manual/Automated) to raw_nap segment
    #specify the config file for epoching parameters (scoring window, segment length, group map)
    epoch_cfg = pipeline_cfg["epoching"]
    segment_length = epoch_cfg["segment_length"]
    #create fixed-length epochs for wake and passive phases (since they don't have annotations)
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
    
    #attach sleep annotations to raw_nap and create epochs based on those annotations
    raw_nap = attach_sleep_annotations(
        raw_nap,
        subject,
        paths,
        epoch_len=30,
        tolerance=5
    )
    # ---- Validate annotation labels ----
    allowed = {"W", "N1", "N2", "N3", "R"}

    labels = set(raw_nap.annotations.description)

    if not labels.issubset(allowed):
        print(f"[WARNING] Unexpected sleep labels detected: {labels - allowed}")
        unexpected = labels - allowed

        if unexpected:
            print(f"[WARNING] Unexpected sleep labels: {unexpected}")


    events, event_id = segment_sleep_annotations_to_events(
    raw_nap,
    raw_nap.annotations, # check if these are indeed only sleep-based annotations or if we need to filter them first
    segment_length= epoch_cfg["segment_length"],
    group_map= epoch_cfg["group_map"],
)
    # create epochs based on sleep annotations
    epochs_nap = create_sleep_epochs(
        raw_nap,
        events,
        event_id,
        segment_length=10
    )

    check_epoch_groups(epochs_nap)

    qc_row = compute_epoch_qc(
        subject,
        phases,
        epochs_all,
        raw_nap
    )

    save_subject_qc(qc_row, subject, report_root)

    plot_hypnogram(subject, raw_nap, report_root)
    add_hypnogram_to_report(report, subject, raw_nap)

    #Add epoch summary to report
    add_epoch_summary(report, epochs_all)
    
    # # 5) Clean epochs by group using NICE/adaptive/autoreject
    # epochs_clean, cleaning_info = run_nice_cleaning_by_group(
    #     epochs,
    #     group_map,
    #     pipeline_cfg["cleaning"]
    # )

    # # 6) Apply bad channels/epochs to raw & epochs
    # raw_clean, epochs_final = apply_bad_channels_and_epochs(
    #     raw,
    #     epochs,
    #     epochs_clean,
    #     out_dir
    # )

    # 7) QC report
    #add_preproc_to_report(report, raw_clean, epochs_final, cleaning_info, out_dir)
    report_path = report_dir / f"sub-{subject_id}_{pipe_name}_report.html"
    save_report(report, report_path)

    # 8) Save summary info / logs / CSV
    update_master_results(subject_id, pipe_name, cleaning_info, logs_dir, errors_dir)

    # save MNE report 
    save_report(report, report_file)