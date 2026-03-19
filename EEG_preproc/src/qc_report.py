import mne
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def init_report(subject, report_root):

    report_dir = Path(report_root) / f"sub-{subject}"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"sub-{subject}_preproc_report.html"

    report = mne.Report(
        title=f"EEG preprocessing report — sub-{subject}",
        verbose=False
    )

    return report, report_file


def add_raw_overview(report, raw):

    report.add_raw(
        raw=raw,
        title="Raw data overview",
        psd=False
    )


def add_psd_section(report, raw, phase_name, fmax=60):

    fig = raw.compute_psd(fmax=fmax).plot(show=False)

    report.add_figure(
        fig,
        title=f"{phase_name} – Power spectral density",
        section="Filtering QC"
    )

def add_filter_comparison(report, raw_before, raw_after, filter_cfg, fmax=60):

    # --------------------------------
    # filtering metadata table
    # --------------------------------

    rows = [
        {"Parameter": "Filter type", "Value": "FIR (MNE default)"},
        {"Parameter": "High-pass (Hz)", "Value": filter_cfg["l_freq"]},
        {"Parameter": "Low-pass (Hz)", "Value": filter_cfg["h_freq"]},
        {"Parameter": "Resampled to (Hz)", "Value": raw_after.info["sfreq"]},
    ]

    df = pd.DataFrame(rows)

    report.add_html(
        df.to_html(index=False),
        title="Filtering parameters",
        section="Filtering QC"
    )

    fig_before = raw_before.compute_psd(fmax=fmax).plot(show=False)
    fig_after = raw_after.compute_psd(fmax=fmax).plot(show=False)

    report.add_figure(
        fig_before,
        title="PSD before filtering",
        section="Filtering QC"
    )

    report.add_figure(
        fig_after,
        title="PSD after filtering",
        section="Filtering QC"
    )


def add_segment_summary(report, phases):

    rows = []

    for segment_name, raw_segment in phases.items():

        start_s = raw_segment.first_time
        end_s = raw_segment.times[-1] + start_s
        duration_s = end_s - start_s

        rows.append({
            "Segment": segment_name,
            "Start (s)": round(start_s, 2),
            "End (s)": round(end_s, 2),
            "Duration (min)": round(duration_s / 60, 2),
            "Samples": raw_segment.n_times
        })

    df = pd.DataFrame(rows)

    report.add_html(
        df.to_html(index=False, classes="table table-striped"),
        title="Recording segments",
        section="Segmentation QC"
    )

def add_hypnogram_to_report(report, fig):

    report.add_figure(
        fig,
        title="Nap hypnogram",
        section="Sleep staging QC"
    )

def add_nap_stage_distribution(report, raw_nap):

    allowed = ["Wake", "N1", "N2", "N3", "R"]

    ann = raw_nap.annotations

    # count stage occurrences
    stage_counts = {stage: 0 for stage in allowed}

    for desc in ann.description:
        if desc in stage_counts:
            stage_counts[desc] += 1

    total = sum(stage_counts.values())

    if total == 0:
        print("[WARNING] No sleep stages found in nap annotations")
        return

    rows = []

    for stage in allowed:
        pct = (stage_counts[stage] / total) * 100

        rows.append({
            "Stage": stage,
            "Percent (%)": round(pct, 1)
        })

    df = pd.DataFrame(rows)

    report.add_html(
        df.to_html(index=False),
        title="Nap sleep stage distribution",
        section="Sleep staging QC"
    )

def add_bad_epoch_matrix(report, epochs, bad_epochs, subject_id, phase_name):

    import numpy as np

    n_epochs = len(epochs)

    matrix = np.zeros((1, n_epochs))
    matrix[0, bad_epochs] = 1

    fig, ax = plt.subplots(figsize=(12, 2))

    ax.imshow(matrix, aspect="auto", cmap="Reds")

    ax.set_title(f"{subject_id} | {phase_name} – Bad epoch matrix")
    ax.set_xlabel("Epoch index")
    ax.set_yticks([])

    report.add_figure(
        fig,
        title=f"{phase_name} – Bad epoch matrix",
        section="NICE Cleaning QC"
    )

    plt.close(fig)

def add_bad_channel_topomap(report, raw, bad_channels, phase_name):

    if len(bad_channels) == 0:
        return

    fig = raw.plot_sensors(
        kind="topomap",
        show=False
    )

    report.add_figure(
        fig,
        title=f"{phase_name} – Bad channel topomap ({len(bad_channels)})",
        section="NICE Cleaning QC"
    )

    plt.close(fig)

def add_channel_variance(report, raw, phase_name):

    data = raw.get_data(picks="eeg")

    variances = data.var(axis=1)

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.hist(variances, bins=40)

    ax.set_title(f"{phase_name} – Channel variance distribution")
    ax.set_xlabel("Variance")
    ax.set_ylabel("Channel count")

    report.add_figure(
        fig,
        title=f"{phase_name} – Channel variance distribution",
        section="NICE Cleaning QC"
    )

    plt.close(fig)

def save_report(report, report_file):

    report.save(
        report_file,
        overwrite=True,
        open_browser=False
    )

    print(f"Report saved: {report_file}")
