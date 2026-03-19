import pandas as pd
from datetime import datetime
from pathlib import Path

def update_master_results(subject_id, pipeline_name, cleaning_info, logs_dir):

    logs_dir = Path(logs_dir)
    logs_dir.mkdir(exist_ok=True, parents=True)

    master_file = logs_dir / f"{pipeline_name}_cleaning_summary.csv"

    rows = []

    # for session, metrics in cleaning_info.items():

    #     rows.append({
    #         "subject": subject_id,
    #         "session": session,
    #         "bad_channel_count": metrics["bad_channel_count"],
    #         "bad_epoch_count": metrics["bad_epoch_count"],
    #         "bad_channels": ",".join(metrics["bad_channels"])
    #     })

    df_new = pd.DataFrame(rows)

    if master_file.exists():
        df_new.to_csv(master_file, mode="a", header=False, index=False)
    else:
        df_new.to_csv(master_file, index=False)
    
def log_failed_subject(
    subject_id,
    pipeline_name,
    error_stage,
    error_message,
    errors_dir,
):
    """
    Log failed preprocessing subjects.
    """

    errors_dir = Path(errors_dir)
    errors_dir.mkdir(parents=True, exist_ok=True)

    error_file = errors_dir / "failed_preproc.csv"

    row = {
        "subject": subject_id,
        "pipeline": pipeline_name,
        "stage": error_stage,
        "error_message": str(error_message),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    df_row = pd.DataFrame([row])

    if error_file.exists():
        df_row.to_csv(error_file, mode="a", header=False, index=False)
    else:
        df_row.to_csv(error_file, index=False)

    print(f"[ERROR LOGGED] {subject_id} → {error_file}")