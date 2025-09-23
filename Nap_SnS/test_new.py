# --- Pure Python version using pygame and keyboard ---
import os
import pandas as pd
import time
import pygame
import keyboard
from datetime import datetime

# --- Parameters ---
resume_flag = False
input_rep_folder = 'input/rep_concatenated_8times'
output_folder = 'output'
participant = input("Enter participant ID: ") if resume_flag else f"{int(time.time())}"
session = input("Enter session ID: ") if resume_flag else '001'
date_str = datetime.now().strftime('%Y-%m-%d')
output_path = os.path.join(output_folder, f"{participant}_speech2song_{date_str}", session)
os.makedirs(output_path, exist_ok=True)

stimulus_delay = 5
volume = 1.0

# --- Load sound list ---
play_xlsx_nap = os.path.join(output_path, 'nap_sns_list.xlsx')
sound_list_nap_b1 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_1')
sound_list_nap_b2 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_2')
sound_list_nap_b3 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_3')

# --- Initialize audio ---
pygame.mixer.init()
pygame.mixer.music.set_volume(volume)

# --- Function to play a sound with pause/resume ---
def play_sound(sound_path):
    pygame.mixer.music.load(sound_path)
    pygame.mixer.music.play()
    start_time = time.time()
    paused_time = 0
    paused = False

    while pygame.mixer.music.get_busy():
        if keyboard.is_pressed('space'):
            if not paused:
                pygame.mixer.music.pause()
                paused = True
                pause_start = time.time()
                print("Paused. Press SPACE to resume.")
                time.sleep(0.3)  # debounce
            else:
                pygame.mixer.music.unpause()
                paused = False
                paused_time += time.time() - pause_start
                print("Resumed.")
                time.sleep(0.3)
        if keyboard.is_pressed('esc'):
            pygame.mixer.music.stop()
            return False
        time.sleep(0.05)
    return True

# --- Block playback function ---
def play_block(sound_df, block_name):
    print(f"\n--- Playing Block: {block_name} ---")
    played, unplayed = [], []

    for idx, row in sound_df.iterrows():
        cur_sound_path = os.path.join(input_rep_folder, row['type'], row['sound'])
        print(f"Playing: {row['sound']}")
        if os.path.exists(cur_sound_path):
            success = play_sound(cur_sound_path)
            if success:
                played.append(row['sound'])
                time.sleep(stimulus_delay)
            else:
                unplayed.append(row['sound'])
                break
        else:
            print(f"Missing file: {cur_sound_path}")
            unplayed.append(row['sound'])

    df_log = pd.DataFrame({
        'played': played + [''] * (len(unplayed)),
        'unplayed': unplayed + [''] * (len(played) - len(unplayed))
    })
    log_path = os.path.join(output_path, f"{block_name}_log.csv")
    df_log.to_csv(log_path, index=False)
    print(f"Saved log to: {log_path}")

# --- Main session flow ---
blocks = [(sound_list_nap_b1, 'Nap_Block_1'),
          (sound_list_nap_b2, 'Nap_Block_2'),
          (sound_list_nap_b3, 'Nap_Block_3')]

start_block = 1
if resume_flag:
    try:
        start_block = int(input("From which block to resume? (1, 2, 3): "))
    except:
        print("Invalid input. Starting from Block 1.")

for i, (df, name) in enumerate(blocks[start_block-1:], start=start_block):
    play_block(df, name)
    if i < 3:
        cont = input(f"Continue to Block {i+1}? (y/n): ").strip().lower()
        if cont != 'y':
            print("Session ended early.")
            break

print("Session complete.")
