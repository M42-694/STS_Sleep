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

plugins.activatePlugins()
prefs.hardware['audioLib'] = [ 'PTB', 'sounddevice','pyo', 'pygame'] #'ptb' ['PTB']
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

def core_wait_with_esc(wait_time):
	# Custom loop to replace core.wait() and check for Esc press
	start_time = core.getTime()
	while core.getTime() - start_time < wait_time:
		keys = event.getKeys()  # Get any key presses
		if 'escape' in keys:    # If 'Esc' key is pressed
			core.quit()         # Quit PsychoPy
		core.wait(0.01)  		# Small wait to reduce CPU usage

##===== triggers SETUP =====###
import serial.tools.list_ports
ports=serial.tools.list_ports.comports()
for port,desc,hwid in ports:
    print(f"Port: {port}, Description: {desc},HWID:{hwid}")
SerialPortObj = None
def cleanup_serial(): #can go in utils
    global SerialPortObj
    if SerialPortObj and SerialPortObj.is_open:
        SerialPortObj.close()
        print("Serial port closed on exit.")

def setup_serial(): #can go in utils
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
reset_trigger_code = b'\x00'
start_session = b'\x15'
stop_session = b'\x63'

instruction_trigger = b'\x37'  # for all instruction slides
song_trigger = b'\x0B'         # for all song stimuli
speech_trigger = b'\x0C'

if trigger:
    # select here the address of your port
    setup_serial()

################################
# --- Parameter to control --- #
################################
# param exp
psychopyVersion = '2024.2.4'
expName = 'speech2song'
input_rep_folder = 'input/rep_concatenated_8times'

## Create folders and logging files
# ensure that relative paths start from the same directory as this script
_thisDir = op.dirname(op.abspath(__file__))
os.chdir(_thisDir)
# create output folder for this subject and session and determine filename
expInfo = {'participant': '',
            'session': ''}
expInfo['date'] = datetime.now().strftime('%Y-%m-%d') 
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

######################
## --- Init window --- ##
######################
# create window and fixation cross
win_size = (1280, 720) # (800, 600) # [1920, 1080]
ratio_text_size = 40
ratio_text_width= 1
ratio_cross = 40
contrast = 1
full_screen = True
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

def play_sound_block(sound_list_df, input_folder, output_log, block_name):
    played_stimuli = []
    unplayed_stimuli = []

    print(f"\n--- Playing Block: {block_name} ---")
    print("Press SPACE to pause/resume playback.")
    print("Press ESC to exit this block early.\n")

    sound_indices = list(range(len(sound_list_df)))
    current_index = 0
    paused = False

    while current_index < len(sound_indices):
        if not paused:
            idx = sound_indices[current_index]
            cur_sound_name = sound_list_df['sound'][idx]
            cur_type = sound_list_df['type'][idx]
            cur_sound_path = os.path.join(_thisDir, input_rep_folder, cur_type, cur_sound_name)

            
            try:
                mySound = sound.Sound(cur_sound_path, preBuffer=-1, volume=volume)
                mySound.play()
                print(f"Playing: {cur_sound_name}")
                core.wait(mySound.getDuration())
                played_stimuli.append(cur_sound_name)
            except Exception as e:
                print(f"Error playing sound {cur_sound_name}: {e}")
                unplayed_stimuli.append(cur_sound_name)

            core.wait(stimulus_delay)  # Delay between sounds
            current_index += 1

        # Check for key events
        keys = event.getKeys()
        if 'space' in keys:
            paused = not paused
            print("Playback paused." if paused else "Playback resumed.")
            core.wait(0.5)  # debounce
        if 'escape' in keys:
            print("Exiting block early.")
            unplayed_stimuli.extend(
                list(sound_list_df['sound'])[current_index:]
            )
            break

    # Save block-wise log
    log_df = pd.DataFrame({
        'played': played_stimuli + [''] * (len(unplayed_stimuli)),
        'unplayed': unplayed_stimuli + [''] * (len(played_stimuli) - len(unplayed_stimuli))
    })
    log_filename = os.path.join(output_log, f"{block_name}_play_log.csv")
    log_df.to_csv(log_filename, index=False)
    print(f"Saved log for {block_name} to: {log_filename}")
    
# Ensure output_log directory exists
os.makedirs(output_path, exist_ok=True)

# Play Block 1
play_sound_block(sound_list_nap_b1, input_rep_folder, output_path, 'Nap_Block_1')
next_block = gui.Dlg(title="Continue?").addText('Continue to Block 2?').addField('Yes/No:', choices=['Yes', 'No']).show()[0]
if next_block != 'Yes':
    core.quit()

# Play Block 2
play_sound_block(sound_list_nap_b2, input_rep_folder, output_path, 'Nap_Block_2')
next_block = gui.Dlg(title="Continue?").addText('Continue to Block 3?').addField('Yes/No:', choices=['Yes', 'No']).show()[0]
if next_block != 'Yes':
    core.quit()

# Play Block 3
play_sound_block(sound_list_nap_b3, input_rep_folder, output_path, 'Nap_Block_3')


#-----------------------
# End of Nap session 
#------------------------
print(f"All blocks played!")
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
# END
#------------------------


# Play Block 1
play_sound_block(sound_list_nap_b1, input_folder, output_path, 'Nap_Block_1')
msg = visual.TextStim(win, text="Continue to Block 2?\nPress 'y' for Yes, 'n' for No.", height=0.07)
msg.draw()
win.flip()

key = event.waitKeys(keyList=['y', 'n', 'escape'])[0]

if key == 'escape' or key == 'n':
    core.quit()

# Play Block 2
play_sound_block(sound_list_nap_b2, input_folder, output_path, 'Nap_Block_2')
msg = visual.TextStim(win, text="Continue to Block 2?\nPress 'y' for Yes, 'n' for No.", height=0.07)
msg.draw()
win.flip()

key = event.waitKeys(keyList=['y', 'n', 'escape'])[0]

if key == 'escape' or key == 'n':
    core.quit()

# Play Block 3
play_sound_block(sound_list_nap_b3, input_folder, output_path, 'Nap_Block_3')

#-----------------------
# End of Nap session 
#------------------------
print(f"All blocks played!")
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)