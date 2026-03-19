from datetime import datetime
import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt


def compute_epoch_qc(subject, phases, epochs_all, raw_nap):

    qc = {"subject": subject}

    # -----------------------------
    # Phase durations
    # -----------------------------
    for phase, raw_phase in phases.items():
        qc[f"{phase}_dur_s"] = round(raw_phase.times[-1], 2)

    # -----------------------------
    # Epoch counts per phase
    # -----------------------------
    for phase, epochs in epochs_all.items():
        qc[f"{phase}_epo"] = len(epochs)

    # -----------------------------
    # Sleep stage durations
    # -----------------------------
    stage_dur = {}

    for onset, dur, desc in zip(
        raw_nap.annotations.onset,
        raw_nap.annotations.duration,
        raw_nap.annotations.description,
    ):
        stage_dur[desc] = stage_dur.get(desc, 0) + dur

    for s in ["Wake", "N1", "N2", "N3", "R"]:
        qc[f"{s}_dur_s"] = round(stage_dur.get(s, 0), 2)

    # -----------------------------
    # Stage annotation counts
    # -----------------------------
    stage_counts = Counter(raw_nap.annotations.description)

    for s in ["Wake", "N1", "N2", "N3", "R"]:
        qc[f"{s}_epochs"] = stage_counts.get(s, 0)

    return qc

def save_subject_qc(qc_row, subject, report_root):

    sub_dir = report_root / f"sub-{subject}"
    sub_dir.mkdir(parents=True, exist_ok=True)

    qc_file = sub_dir / "epoch_qc_summary.csv"

    df = pd.DataFrame([qc_row])

    df.to_csv(qc_file, index=False)

def plot_hypnogram(subject, raw_nap, report_root):

    ann = raw_nap.annotations

    stage_map = {
        "Wake": 0,
        "N1": -1,
        "N2": -2,
        "N3": -3,
        "R": 1,
    }

    times = []
    stages = []

    for onset, dur, desc in zip(ann.onset, ann.duration, ann.description):

        if desc not in stage_map:
            continue

        start = onset / 60
        end = (onset + dur) / 60
        val = stage_map[desc]

        if not times:
            # first stage
            times.append(start)
            stages.append(val)

        times.append(end)
        stages.append(val)

    fig, ax = plt.subplots(figsize=(10, 3))

    ax.step(times, stages, where="post", linewidth=2)

    ax.set_yticks([1, 0, -1, -2, -3])
    ax.set_yticklabels(["REM", "W", "N1", "N2", "N3"])

    ax.set_xlabel("Time (minutes)")
    ax.set_title(f"Nap Hypnogram – sub-{subject}")

    ax.set_ylim(1.5, -3.5)
    ax.set_xticks(np.arange(0, raw_nap.times[-1]/60 + 5, 5))
    ax.grid(True, axis="x", alpha=0.3)

    # -------- save PNG --------

    sub_dir = report_root / f"sub-{subject}"
    sub_dir.mkdir(parents=True, exist_ok=True)

    out_file = sub_dir / f"nap_hypnogram - sub-{subject}.png"

    fig.savefig(out_file, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return fig

def log_warning(subject, report_root, message):

    sub_dir = report_root / f"sub-{subject}"
    sub_dir.mkdir(parents=True, exist_ok=True)

    log_file = sub_dir / "warnings.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")