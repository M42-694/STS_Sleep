from pathlib import Path
import mne

SLEEP_STAGE_LABELS = {"W", "N1", "N2", "N3", "R"}

def attach_sleep_annotations(raw_nap, subject, paths, epoch_len=30, tolerance=0.1):

    """
    Attach sleep stage annotations to nap raw object.

    Performs:
    - duration alignment check
    - epoch count comparison
    - error logging

    Returns
    -------
    raw_nap_with_annotations or None
    """

    sub_name = f"sub-{subject}"

    annot_path = (
        Path(paths["sleep_annotations_root"])
        / sub_name
        / f"{sub_name}_ses-nap_task-sleep_desc-sleepstage_annotations.fif"
    )

    errors_dir = Path(paths["errors_root"])
    errors_dir.mkdir(parents=True, exist_ok=True)

    error_log = errors_dir / "sleep_annotation_errors.log"

    try:

        annot_raw = mne.io.read_raw_fif(annot_path, preload=False)

        # -------- duration comparison --------
        raw_duration = raw_nap.times[-1]

        annot_duration = annot_raw.times[-1]

        duration_diff = abs(raw_duration - annot_duration)

        # -------- epoch comparison --------
        expected_epochs = int(raw_duration / epoch_len)
        actual_epochs = int(annot_duration / epoch_len)

        epoch_diff = expected_epochs - actual_epochs

        # -------- check duration mismatch --------
        if duration_diff > tolerance:

            with open(error_log, "a") as f:
                f.write(
                    f"{sub_name} | Duration mismatch | "
                    f"raw={raw_duration:.2f}s | "
                    f"annot={annot_duration:.2f}s | "
                    f"diff={duration_diff:.2f}s | "
                    f"expected_epochs={expected_epochs} | "
                    f"annot_epochs={actual_epochs}\n"
                )

            return None

        # attach annotations if duration is valid
        raw_nap.set_annotations(annot_raw.annotations)

        # -------- record epoch mismatch warning --------
        if epoch_diff != 0:

            with open(error_log, "a") as f:
                f.write(
                    f"{sub_name} | Epoch mismatch | "
                    f"expected_epochs={expected_epochs} | "
                    f"annot_epochs={actual_epochs} | "
                    f"diff={epoch_diff}\n"
                )

        return raw_nap

    except Exception as e:

        with open(error_log, "a") as f:

            f.write(f"{sub_name} | Annotation load error | {str(e)}\n")
            log_warning(subject, paths["report_root"], f"Annotation load error for {sub_name}: {str(e)}")

            return None

