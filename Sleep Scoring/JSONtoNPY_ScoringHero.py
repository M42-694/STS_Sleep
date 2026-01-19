#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 11:36:56 2026

@author: clara
"""

import os
import json
import glob
import numpy as np

# folder containing the json files
data_dir = '/Users/clara/Documents/Sleep Scoring/Clara Scores'

# find all matching files
json_files = glob.glob(
    os.path.join(data_dir, 'STS_Sleep*_Nap-edf.json')
)

for path in json_files:
    # open and load json
    with open(path, "r") as f:
        data = json.load(f)

    # get the list of epoch dictionaries
    epochs = data[0]

    # extract the stage strings
    stages = np.array([ep["stage"] for ep in epochs], dtype=str)

    # create output filename (.npy)
    base_name = os.path.splitext(os.path.basename(path))[0]
    output_path = os.path.join(data_dir, f"{base_name}.npy")

    # save
    np.save(output_path, stages)

    print(f"Saved: {output_path}")
