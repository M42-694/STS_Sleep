import mne
from mne.preprocessing import ICA
from mne_icalabel import label_components
from pathlib import Path


def run_ica_cleaning(
    raw,
    epochs_all,
    session_type,
    subject_id,
    pipeline_cfg,
    paths,
    report=None
):

    epochs_wake1 = epochs_all["wake1"]
    epochs_wake2 = epochs_all["wake2"]
    epochs_passive = epochs_all["passive"]
    epochs_nap_wake = epochs_all["nap"]["Group1"]

    epochs_list = [
            epochs_wake1,
            epochs_wake2,
            epochs_passive,
            epochs_nap_wake
        ]
    epochs_wake = mne.concatenate_raws(epochs_list, add_offset=True)
    epochs_ica = epochs_wake.copy().filter(
            l_freq=ica_cfg["l_freq"],
            h_freq=ica_cfg["h_freq"]
        )
        

    # ---------------------------------------
    # Choose epochs used for ICA fitting
    # ---------------------------------------

    if session_type == "nap":
        epochs_fit = epochs_ica["Group1"].copy()
    else:
        epochs_fit = epochs.copy()

    # filter for ICA fit
    epochs_fit = epochs_fit.filter(
        l_freq=ica_cfg["fit_filter"]["l_freq"],
        h_freq=ica_cfg["fit_filter"]["h_freq"]
    )

    # ---------------------------------------
    # Fit ICA
    # ---------------------------------------

    ica = ICA(
        n_components=ica_cfg["n_components"],
        method=ica_cfg["method"],
        random_state=ica_cfg["random_state"],
        max_iter=ica_cfg["max_iter"],
        fit_params=dict(extended=ica_cfg["extended"])
    )

    ica.fit(epochs_fit)

    # ---------------------------------------
    # Label components
    # ---------------------------------------

    ic_labels = label_components(
        epochs_fit,
        ica,
        method="iclabel"
    )

    labels = ic_labels["labels"]

    exclude_labels = ica_cfg["exclude_labels"]

    exclude_idx = [
        i for i, label in enumerate(labels)
        if label in exclude_labels
    ]

    ica.exclude = exclude_idx

    # ---------------------------------------
    # Apply ICA
    # ---------------------------------------

    if session_type == "nap":

        epochs_wake = epochs["Group1"]

        ica.apply(epochs_wake)

    else:

        ica.apply(raw)

    # ---------------------------------------
    # Save ICA object
    # ---------------------------------------

    deriv_root = Path(paths["deriv_root"]) / "preproc_legacy"
    out_dir = deriv_root / f"sub-{subject_id}" / session_type
    out_dir.mkdir(parents=True, exist_ok=True)

    ica_file = out_dir / f"sub-{subject_id}_session-{session_type}_ica.fif"

    ica.save(ica_file)

    # ---------------------------------------
    # Save ICA sources
    # ---------------------------------------

    sources = ica.get_sources(epochs_fit)

    src_file = out_dir / f"sub-{subject_id}_session-{session_type}_ica-sources.fif"

    sources.save(src_file)

    # ---------------------------------------
    # Report figures
    # ---------------------------------------

    if report is not None:

        fig = ica.plot_components(show=False)

        report.add_figure(
            fig,
            title=f"{session_type} – ICA components",
            section="ICA QC"
        )

    # ---------------------------------------
    # QC metrics
    # ---------------------------------------

    qc = {
        "subject": subject_id,
        "session": session_type,
        "excluded_components": exclude_idx
    }

    return raw, qc