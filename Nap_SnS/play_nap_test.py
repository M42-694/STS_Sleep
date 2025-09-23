# --- Import packages ---
from numpy.random import random
import pandas as pd
import numpy as np
import os 
import random
import math
import os.path as op

from psychopy import prefs
from psychopy import plugins
from psychopy import sound, gui, visual, core, data, event, logging
from psychopy.event import Mouse
from psychopy.hardware import keyboard
from datetime import datetime
import serial
import atexit
import serial.tools.list_ports

plugins.activatePlugins()
prefs.hardware['audioLib'] =  [ 'PTB', 'sounddevice','pyo', 'pygame'] #'ptb' ['PTB']
#prefs.hardware['audioDevice'] = 'MOTU M Series'  
prefs.hardware['sampleRate'] = 22050
prefs.hardware['audioLatencyMode'] = '0'
defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')
#defaultKeyboard = keyboard.Keyboard()

from utils.slider_routine_discrete import slider_routine_discrete
from utils.slider_routine_discrete_key import slider_routine_discrete_key
from utils.slider_routine_continuous import slider_routine_continuous
from utils.slider_routine_continuous_key import slider_routine_continuous_key
from utils.utils import *

##===== triggers SETUP =====###

ports=serial.tools.list_ports.comports()

for port,desc,hwid in ports:
    print(f"Port: {port}, Description: {desc},HWID:{hwid}")
SerialPortObj = None

def cleanup_serial():
    global SerialPortObj
    if SerialPortObj and SerialPortObj.is_open:
        SerialPortObj.close()
        print("Serial port closed on exit.")
def setup_serial():
    global SerialPortObj
    try:
        SerialPortObj = serial.Serial("COM6", baudrate=115200, timeout=1)
        print("Serial port COM6 opened successfully.")
        atexit.register(cleanup_serial)
    except serial.SerialException as e:
        print(f"[Serial Init Error] Could not open COM6: {e}")
        SerialPortObj = None
        

# Set Trigger initialisation 
trigger = False
port_name = 'COM6'
#trigger codes
reset_trigger_code = b'\x30' # 0
start_session = b'\x31' #1
stop_session = b'\x39'  #9

instruction_trigger = b'\x32'  # 2 - for all instruction slides
song_trigger = b'\x35'         # 5 for all song stimuli
speech_trigger = b'\x36'       # 6 for speech stimuli
pause_trigger =  b'\x50'  # P for pause
resume_trigger = b'\x52' #  R for resume
if trigger:
    # select here the address of your port
    setup_serial()

################################
# --- Parameter to control --- #
################################
# param exp
psychopyVersion = '2024.2.4'
expName = 'speech2song'
input_folder = 'input/stimuli/'
resume_flag = False

# control mode
control_mode = 'key'   # 'key' for keyboard, 'mouse' for mouse
continue_key = 'return'  # 'return' for Enter, 'down' for ↓

# Store info about the participant and experiment session
if not resume_flag:
    expInfo = {'participant': f"{np.random.randint(0, 999999):06.0f}",
            'session': '001'}
else:  # resume mode: must input participant
    expInfo = {'participant': '',
            'session': ''}    
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = datetime.now().strftime('%Y-%m-%d')
expInfo['expName'] = expName
expInfo['psychopyVersion'] = psychopyVersion
## Create folders and logging files
# ensure that relative paths start from the same directory as this script
_thisDir = op.dirname(op.abspath(__file__))
os.chdir(_thisDir)
# create output folder for this subject and session and determine filename
filename = u'%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
output_path = _thisDir + os.sep + u'output/%s_%s_%s/%s' % (expInfo['participant'], expName, expInfo['date'],expInfo['session'])
if not resume_flag:
    os.makedirs(output_path, exist_ok=True)
types = ["song", "speech"]     # illusion - song, control - speech
# debug
resume_flag = False
test_mode = True
test_n_stimulus = 5

# sound presentation
n_repeat = 8               # repetition time of stimulus
gap_time = 0.5             # the interval between repetition (sec)
n_blocks = 3
stimulus_delay = 5  # Change this as needed during piloting
# control mode
control_mode = 'key'   # 'key' for keyboard, 'mouse' for mouse
################################
#Load from the nap stimulus list from the existing participant output directory
################################

play_xlsx_nap = op.join(output_path,'nap_sns_list.xlsx')
sound_list_nap_b1 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_1')
sound_list_nap_b2 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_2')
sound_list_nap_b3 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_3')

## --- Define the stimulus list for each session --- ##
n_stimulus_b1 = len(sound_list_nap_b1)
n_stimulus_b2 = len(sound_list_nap_b2)
n_stimulus_b3 = len(sound_list_nap_b3)

# add properties of sound_list_nap and sound_list_wake
file_list_b1 = sound_list_nap_b1['sound']
sound_type_b1 = sound_list_nap_b1['type']
file_list_b2 = sound_list_nap_b2['sound']
sound_type_b2 = sound_list_nap_b2['type']
file_list_b3 = sound_list_nap_b3['sound']
sound_type_b3 = sound_list_nap_b3['type']

print("Loaded sound_list_nap_b1,sound_list_nap_b2 and sound_list_nap_b3 from file.")

def core_wait_with_esc(wait_time):
    # Custom loop to replace core.wait() and check for Esc press
    start_time = core.getTime()
    while core.getTime() - start_time < wait_time:
        keys = event.getKeys()  # Get any key presses
        if 'escape' in keys:    # If 'Esc' key is pressed
            SerialPortObj.close()
            # Save block before quitting
            block_data[block_index] = (block_name, sound_list)
            with pd.ExcelWriter(play_xlsx_nap, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                sound_list.to_excel(writer, sheet_name=block_name, index=False)
            print(f"Saved updated log for {block_name} to Excel before quitting.")
            core.quit()  # Quit PsychoPy

        core.wait(0.01)  		# Small wait to reduce CPU usage
        

######################
## --- Init window --- ##
######################
# create window and fixation cross
win_size = (1280, 720) # (800, 600) # [1920, 1080]
ratio_text_size = 40
ratio_text_width= 1
ratio_cross = 40
contrast = 1
full_screen = False
if test_mode:
    full_screen = False

win = visual.Window(
    size=win_size,
    units="pix",
    fullscr=full_screen,
    color=[-1, -1, -1])

# fixation cross
fixation = visual.shape.ShapeStim(win=win, 
								  vertices="cross", 
								  color='white', 
								  fillColor='white', 
								  contrast=contrast, 
								  size=max(win.size)/ratio_cross)

# Adapt text to control mode
if control_mode == 'key':
    end_key_name = continue_key
    control_text = 'Press ' + end_key_name
elif control_mode == 'mouse':
    control_text = 'Click'
    mouse = Mouse(visible=True, newPos=[0,0])
    mouse = event.Mouse(win=win)
# Parameters
N_REP = 8
pause_between_reps = 0.5  # seconds
volume = 0.8

def save_log(played_stimuli, unplayed_stimuli, output_log, block_name):
    os.makedirs(output_log, exist_ok=True)
    log_df = pd.DataFrame({
        'played': played_stimuli + [''] * (len(unplayed_stimuli)),
        'unplayed': unplayed_stimuli + [''] * (len(played_stimuli) - len(unplayed_stimuli))
    })
    log_filename = os.path.join(output_log, f"{block_name}_play_log.csv")
    log_df.to_csv(log_filename, index=False)
    print(f"Saved log for {block_name} to: {log_filename}")

    # Return status dictionary
    status_dict = {s: 'played' for s in played_stimuli}
    status_dict.update({s: 'unplayed' for s in unplayed_stimuli})
    return status_dict

def play_sound_block(sound_list_df, input_folder, output_log, block_name):
    print(f"\n--- Playing Block: {block_name} ---")
    print("Press SPACE to pause/resume playback.")
    print("Press ESC to exit this block early.\n")

    played_stimuli = []
    unplayed_stimuli = []

    sound_indices = list(range(len(sound_list_df)))
    current_index = 0
    paused = False
    def send_trigger(code):
        try:
            SerialPortObj.write(reset_trigger_code)
            core.wait(0.005)
            SerialPortObj.write(code)
            core.wait(0.005)
        except Exception as e:
            print(f"[Trigger Error] Failed to send trigger {code}: {e}")

    while current_index < len(sound_indices):
        idx = sound_indices[current_index]
        cur_sound_name = sound_list_df['sound'][idx]
        cur_type = sound_list_df['type'][idx]
        cur_sound_path = os.path.join(_thisDir, input_folder, cur_type, cur_sound_name)

        try:
            mySound = sound.Sound(cur_sound_path, preBuffer=-1, volume=volume)
            core_wait_with_esc(mySound.getDuration()+0.1)
        except Exception as e:
            print(f"Error loading sound {cur_sound_name}: {e}")
            unplayed_stimuli.append(cur_sound_name)
            current_index += 1
            continue

        print(f"Playing: {cur_sound_name} (x{N_REP})")
        rep = 0
        pause_log = {}  # {sound_name: [rep_counts_with_pause]}
        while rep < N_REP:
            # Check if paused
            keys = event.getKeys()
            if 'escape' in keys:
                print("Exiting block early.")
                unplayed_stimuli.extend(sound_list_df['sound'][current_index:])
                save_log(played_stimuli, unplayed_stimuli, output_log, block_name)
                return played_stimuli, unplayed_stimuli, pause_log

            if 'space' in keys:
                paused = not paused
                if paused:
                    print("Paused.")
                    if trigger:
                        send_trigger(pause_trigger)

                    # Log the pause for this sound at this rep
                    if cur_sound_name not in pause_log:
                        pause_log[cur_sound_name] = []
                    pause_log[cur_sound_name].append(rep + 1)  # 1-based rep index

                else:
                    print("Resumed.")
                    if trigger:
                        send_trigger(resume_trigger)
                core.wait(0.3)

            if paused:
                core.wait(0.1)
                continue

            # Play sound
            if cur_type.lower() == 'song':
                if trigger:
                    send_trigger(song_trigger)
            elif cur_type.lower() == 'speech':
                if trigger:
                    send_trigger(speech_trigger)
            else:
                print(f"Unknown stimulus type: {cur_type}, no trigger sent.")

            mySound.play()
            core.wait(mySound.getDuration())

            # Wait for inter-stimulus pause (but check for pause/escape)
            t_start = core.getTime()
            while core.getTime() - t_start < pause_between_reps:
                keys = event.getKeys()
                if 'escape' in keys:
                    print("Exiting block early.")
                    unplayed_stimuli.extend(sound_list_df['sound'][current_index:])
                    save_log(played_stimuli, unplayed_stimuli, output_log, block_name)
                    # Save block before quitting
                    block_data[block_index] = (block_name, sound_list)
                    with pd.ExcelWriter(play_xlsx_nap, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        sound_list.to_excel(writer, sheet_name=block_name, index=False)
                    print(f"Saved updated log for {block_name} to Excel before quitting.")
                    return played_stimuli, unplayed_stimuli, pause_log
                elif 'space' in keys:
                    paused = True
                    print("Paused.")
                    core.wait(0.3)
                    break
                core.wait(0.05)

            if not paused:
                rep += 1

        played_stimuli.append(cur_sound_name)
        current_index += 1

    save_log(played_stimuli, unplayed_stimuli, output_log, block_name)
    sound_list_df['played_status'] = sound_list_df['sound'].map(status_dict).fillna('missing')
    return played_stimuli, unplayed_stimuli, pause_log



# Your block sound lists 
block_data = [
    ('Nap_Block_1', sound_list_nap_b1),
    ('Nap_Block_2', sound_list_nap_b2),
    ('Nap_Block_3', sound_list_nap_b3)
]

# Keep track of completed blocks
completed_blocks = set()

def ask_continue(block_number):
    msg = visual.TextStim(win, text=f"Continue to Block {block_number}?\nPress 'y' for Yes, 'n' for No, or 'escape' to jump to a specific block.", height=0.07)
    msg.draw()
    if trigger:
        SerialPortObj.write(reset_trigger_code)
        #SerialPortObj.flush()
        core.wait(0.005)

        SerialPortObj.write(instruction_trigger)
        #SerialPortObj.flush()
        core.wait(0.005)
    win.flip()
    key = event.waitKeys(keyList=['y', 'n', 'escape'])[0]
    return key

def ask_block_choice():
    msg = visual.TextStim(win, text="Enter block number to repeat (1-3), or 'q' to quit:", height=0.07)
    msg.draw()
    if trigger:
        SerialPortObj.write(reset_trigger_code)
        #SerialPortObj.flush()
        core.wait(0.005)

        SerialPortObj.write(instruction_trigger)
        #SerialPortObj.flush()
        core.wait(0.005)
    win.flip()
    key = event.waitKeys(keyList=['1', '2', '3', 'q'])[0]
    return key

# Playback loop
block_index = 0
while block_index < len(block_data):
    block_name, sound_list = block_data[block_index]
    played_stimuli, unplayed_stimuli, pause_log = play_sound_block(sound_list, input_folder, output_path, block_name)
    completed_blocks.add(block_index)
    # === Add additional columns ===
    # 1. played_status
    status_dict = {s: 'played' for s in played_stimuli}
    status_dict.update({s: 'unplayed' for s in unplayed_stimuli})
    sound_list['played_status'] = sound_list['sound'].map(status_dict).fillna('missing')

    # 2. pause_occurred
    sound_list['pause_occurred'] = sound_list['sound'].apply(lambda x: x in pause_log)

    # 3. pause_reps (as comma-separated string)
    sound_list['pause_reps'] = sound_list['sound'].apply(
        lambda x: ','.join(map(str, pause_log.get(x, []))) if x in pause_log else ''
    )

    # === Save updated block back to block_data ===
    block_data[block_index] = (block_name, sound_list)
    with pd.ExcelWriter(play_xlsx_nap, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        sound_list.to_excel(writer, sheet_name=block_name, index=False)
    print(f"Saved updated log for {block_name} to Excel.")
    if block_index < len(block_data) - 1:
        key = ask_continue(block_index + 2)
        if key == 'y':
            block_index += 1
        elif key == 'n':
            # Save block before quitting
            block_data[block_index] = (block_name, sound_list)
            with pd.ExcelWriter(play_xlsx_nap, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                sound_list.to_excel(writer, sheet_name=block_name, index=False)
            print(f"Saved updated log for {block_name} to Excel before quitting.")
            core.quit()
        elif key == 'escape':
            key = ask_block_choice()

            if key == 'q':
                # Save block before quitting
                block_data[block_index] = (block_name, sound_list)
                with pd.ExcelWriter(play_xlsx_nap, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    sound_list.to_excel(writer, sheet_name=block_name, index=False)
                print(f"Saved updated log for {block_name} to Excel before quitting.")
                core.quit()
            else:
                block_index = int(key) - 1  # 1-based to 0-based
    else:
        break  # No more blocks

# Wrap up
print("All blocks played!")
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
# END
#------------------------


