#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 13:50:46 2025

@author: michelle.george
"""

import os
import time
import pandas as pd
from psychopy.sound.backend_ptb import SoundPTB

# ------------ Parameters -------------
input_folder = "input/rep_concatenated_8times"
xlsx_path = "output/participant_speech2song_2025-03-27_14-00-00/session001/nap_sns_list.xlsx"
stimulus_delay = 5  # seconds between sounds
volume = 1.0
sheet_names = ['Nap_Block_1', 'Nap_Block_2', 'Nap_Block_3']

# ------------ Load Blocks -------------
block_lists = [pd.read_excel(xlsx_path, sheet_name=s) for s in sheet_names]

# ------------ Playback Function -------------
def play_block(sound_list, block_num):
    print(f"\n--- Block {block_num} ---")
    print("Press [space] to pause/resume, [esc] to quit\n")

    played, unplayed = [], []

    for i, row in sound_list.iterrows():
        sound_path = os.path.join(input_folder, row['type'], row['sound'])

        if not os.path.exists(sound_path):
            print(f"Missing: {sound_path}")
            unplayed.append(row['sound'])
            continue

        try:
            snd = SoundPTB(value=sound_path, stereo=True, volume=volume)
            snd.play()
            print(f"Playing: {row['sound']}")
        except Exception as e:
            print(f"Error playing {row['sound']}: {e}")
            unplayed.append(row['sound'])
            continue

        paused = False
        while snd.status == SoundPTB.PLAYING:
            if keyboard.is_pressed('space'):
                if not paused:
                    snd.stop()
                    paused = True
                    print("Paused. Press [space] to resume...")
                    while not keyboard.is_pressed('space'):
                        time.sleep(0.1)
                    # Replay from start
                    print("Resuming...")
                    snd = SoundPTB(value=sound_path, stereo=True, volume=volume)
                    snd.play()
            elif keyboard.is_pressed('esc'):
                print("Exiting early.")
                snd.stop()
                unplayed.extend(list(sound_list['sound'])[i + 1:])
                return played, unplayed
            time.sleep(0.05)

        played.append(row['sound'])
        time.sleep(stimulus_delay)

    return played, unplayed

# ------------ Run the Experiment -------------
for i, block_df in enumerate(block_lists):
    played, unplayed = play_block(block_df, i + 1)
    print(f"\nBlock {i+1} done. Played {len(played)}, Skipped {len(unplayed)}.")
    if i < len(block_lists) - 1:
        cont = input("Continue to next block? (y/n): ").strip().lower()
        if cont != 'y':
            break

print("All selected blocks played.")
