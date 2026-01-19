#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manual vs Manual sleep scoring comparison using ScoringHero JSON files

- Single-subject comparison
- Batch comparison across all subjects
- Confusion matrices per participant and across participants
- Cohen's kappa
- Summary CSV

Author: clara & Chat-GPT adapted from michelle's comparescores script
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import confusion_matrix, cohen_kappa_score


# =========================================================
# CONFIGURATION
# =========================================================

STAGE_MAP = {
    "Wake": 0,
    "N1": 1,
    "N2": 2,
    "N3": 3,
    "REM": 4,
    "None": -1
}

STAGE_LABELS = {
    -1: "I",
     0: "W",
     1: "N1",
     2: "N2",
     3: "N3",
     4: "R"
}

ORDERED_LABELS = [-1, 0, 1, 2, 3, 4]


# =========================================================
# LOAD SCORINGHERO JSON
# =========================================================

def load_manual_json(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    epochs = data[0]

    return pd.DataFrame({
        "epoch": [e["epoch"] for e in epochs],
        "stage_str": [e["stage"] for e in epochs],
        "stage_num": [STAGE_MAP.get(e["stage"], -1) for e in epochs]
    })


# =========================================================
# SINGLE-SUBJECT COMPARISON
# =========================================================

def compare_single_subject(json_a, json_b):
    df_a = load_manual_json(json_a)
    df_b = load_manual_json(json_b)

    df = pd.merge(
        df_a, df_b,
        on="epoch",
        suffixes=("_A", "_B"),
        how="inner"
    )

    y_a = df["stage_num_A"].astype(int)
    y_b = df["stage_num_B"].astype(int)

    agreement = (y_a == y_b).mean() * 100
    kappa = cohen_kappa_score(y_a, y_b)

    print("===================================")
    print("Single-subject manual comparison")
    print(f"Epochs compared : {len(df)}")
    print(f"Agreement       : {agreement:.2f}%")
    print(f"Cohen's kappa   : {kappa:.3f}")
    print("===================================")

    return df, agreement, kappa


# =========================================================
# CONFUSION MATRIX
# =========================================================

def save_confusion_matrix(y_a, y_b, subject, out_dir):
    labels = [l for l in ORDERED_LABELS if l in y_a.values or l in y_b.values]
    cm = confusion_matrix(y_a, y_b, labels=labels)
    display_labels = [STAGE_LABELS[l] for l in labels]

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(
                j, i, cm[i, j],
                ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black"
            )

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(display_labels)
    ax.set_yticklabels(display_labels)

    ax.set_xlabel("Scorer B")
    ax.set_ylabel("Scorer A")
    ax.set_title(f"Confusion Matrix — {subject}")

    fig.colorbar(im, ax=ax)
    plt.tight_layout()

    os.makedirs(out_dir, exist_ok=True)
    save_path = os.path.join(out_dir, f"{subject}_cm.png")
    plt.savefig(save_path, dpi=300)
    plt.close(fig)


# =========================================================
# BATCH COMPARISON
# =========================================================

def compare_all_manual_scorers(dir_a, dir_b, output_csv):
    cm_dir = os.path.join(os.path.dirname(output_csv), "Manual_Manual_CM")
    results = []

    # store all epochs across subjects for group-level confusion matrix
    all_y_a = []
    all_y_b = []

    files_a = sorted([f for f in os.listdir(dir_a) if f.endswith(".json")])
    
    for file_a in files_a:
        subject_id = file_a.replace("STS_Sleep", "").replace("_Nap-edf.json", "")
        file_b = f"STS_Sleep{subject_id}_Nap-edf.json"
        path_a = os.path.join(dir_a, file_a)
        path_b = os.path.join(dir_b, file_b)

        if not os.path.exists(path_b):
            print(f"Skipping subject {subject_id}: scorer B file missing")
            continue

        try:
            df_a = load_manual_json(path_a)
            df_b = load_manual_json(path_b)

            df = pd.merge(
                df_a, df_b,
                on="epoch",
                suffixes=("_A", "_B"),
                how="inner"
            )

            y_a = df["stage_num_A"].astype(int)
            y_b = df["stage_num_B"].astype(int)

            agreement = (y_a == y_b).mean() * 100
            kappa = cohen_kappa_score(y_a, y_b)

            save_confusion_matrix(y_a, y_b, subject_id, cm_dir)

            # store for group-level CM
            all_y_a.extend(y_a)
            all_y_b.extend(y_b)

            results.append({
                "Subject": subject_id,
                "Epochs": len(df),
                "Agreement_%": round(agreement, 2),
                "Cohens_kappa": round(kappa, 3)
            })

            # save per-subject epoch-level comparison
            df.to_csv(os.path.join(cm_dir, f"{subject_id}_epoch_comparison.csv"), index=False)

            print(f"✅ Subject {subject_id}: Agreement={agreement:.2f}% | κ={kappa:.3f}")

        except Exception as e:
            print(f"⚠️ Error processing {subject_id}: {e}")

    # --- Create summary CSV with group-level averages ---
    results_df = pd.DataFrame(results)
    avg_epochs = results_df["Epochs"].mean()
    avg_agreement = results_df["Agreement_%"].mean()
    avg_kappa = results_df["Cohens_kappa"].mean()

    # add group-level row
    results_df.loc["Average"] = ["Average", round(avg_epochs, 1), round(avg_agreement, 2), round(avg_kappa, 3)]

    results_df.to_csv(output_csv, index=False)
    print(f"\n💾 Summary saved to {output_csv}")

    # --- Create group-level confusion matrix ---
    if all_y_a and all_y_b:
        labels = [l for l in ORDERED_LABELS if l in all_y_a or l in all_y_b]
        cm = confusion_matrix(all_y_a, all_y_b, labels=labels)
        display_labels = [STAGE_LABELS[l] for l in labels]

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(cm, cmap="Blues")

        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(
                    j, i, cm[i, j],
                    ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black"
                )

        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(display_labels)
        ax.set_yticklabels(display_labels)

        ax.set_xlabel("Scorer B")
        ax.set_ylabel("Scorer A")
        ax.set_title("Group-level Confusion Matrix")

        fig.colorbar(im, ax=ax)
        plt.tight_layout()
        group_cm_path = os.path.join(cm_dir, "group_confusion_matrix.png")
        plt.savefig(group_cm_path, dpi=300)
        plt.close(fig)
        print(f"🎉 Group-level confusion matrix saved to {group_cm_path}")

    return results_df


# =========================================================
# RUN SCRIPT
# =========================================================

if __name__ == "__main__":

    scorer_a_dir = os.path.expanduser("~/Documents/Sleep Scoring/Clara Scores")
    scorer_b_dir = os.path.expanduser("~/Documents/Sleep Scoring/Michelle Scores")

    # single-subject example
    single_subject_id = "01"
    compare_single_subject(
        os.path.join(scorer_a_dir, f"STS_Sleep{single_subject_id}_Nap-edf.json"),
        os.path.join(scorer_b_dir, f"STS_Sleep{single_subject_id}_Nap-edf.json")
    )

    # batch comparison
    output_csv = os.path.join(scorer_a_dir, "../manual_manual_scoring_summary.csv")
    output_csv = os.path.abspath(output_csv)

    summary_df = compare_all_manual_scorers(scorer_a_dir, scorer_b_dir, output_csv)
