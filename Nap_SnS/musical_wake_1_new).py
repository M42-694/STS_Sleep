# --- Import packages ---
from numpy.random import random
import pandas as pd
import numpy as np
import os 
import random
import math
import os.path as op
from psychopy import parallel
import atexit

from psychopy import prefs
from psychopy import plugins
from psychopy import sound, gui, visual, core, data, event, logging
from psychopy.event import Mouse
from psychopy.hardware import keyboard
from datetime import datetime

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

################################
# --- Parameter to control --- #
################################
# param exp
psychopyVersion = '2024.2.4'
expName = 'speech2song'
volumetest_folder = 'input/unlabelled'
input_folder = 'input/stimuli/'
input_rep_folder = 'input/rep_concatenated_8times'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
# debug
resume_flag = False
test_mode = True
test_n_stimulus = 4
# sound presentation
volume = 0.5
record_after = 2           # trial - continuous slider: record time after the sound (sec)
interval_cross_sound = 1   # interval: sound presents after fixation (sec)
n_repeat = 8               # repetition time of stimulus
gap_time = 0.5             # the interval between repetition (sec)
rep_interval_cross_sound = interval_cross_sound # interval: sound presents after click (sec) 
n_breaks = 3
n_breaks_rep = 1
n_blocks = 2
# control mode
control_mode = 'key'   # 'key' for keyboard, 'mouse' for mouse
continue_key = 'return'  # 'return' for Enter, 'down' for ↓
# slider
slider_granularity=.1
slider_decimals=1
step_size = 0.5 # keyboard mode step size
slideSpeed = 50*slider_granularity

# triggers
trigger = True
port_name = 'COM14'
#trigger codes
port_address = '/dev/parport0'
#trigger codes
reset_trigger_code =  0
start_session = 1
stop_session = 9

instruction_trigger =  2 #for all instruction slides
song_trigger = 5 #for all song stimuli
speech_trigger =  6 #for speech stimuli
response_trigger =  7 #for response


    

##############################
#### ___ EXPERIMENT SETUP ____
##############################
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

ParallelPortObj = None

def cleanup_parallel():
    global ParallelPortObj
    if ParallelPortObj is not None:
        try:
            ParallelPortObj.setData(0)  # drop line to 0 on exit
        except Exception:
            pass

def setup_parallel():
    global ParallelPortObj
    try:
        ParallelPortObj = parallel.ParallelPort(address=port_address)
        # ensure known state
        ParallelPortObj.setData(0)
        atexit.register(cleanup_parallel)
        print(f"Parallel port opened at {port_address}.")
    except Exception as e:
        print(f"[Parallel Init Error] Could not open {port_address}: {e}")
        ParallelPortObj = None

def send_trigger(code: int):
    """Short pulse on the data lines: 0 → code → 0."""
    try:
        ParallelPortObj.setData(0)
        core.wait(0.001)
        ParallelPortObj.setData(int(code))
        core.wait(0.005)   # ~5 ms pulse
        ParallelPortObj.setData(0)
    except Exception as e:
        print(f"[Trigger Error] Failed to send trigger {code}: {e}")

def core_wait_with_esc(wait_time):
    # Custom loop to replace core.wait() and check for Esc press
    start_time = core.getTime()
    while core.getTime() - start_time < wait_time:
        keys = event.getKeys()  # Get any key presses
        if 'escape' in keys:    # If 'Esc' key is pressed
            cleanup_parallel()
            core.quit()  # Quit PsychoPy

        core.wait(0.01)  		# Small wait to reduce CPU usage
if trigger:
    # select here the address of your port
    setup_parallel()
def core_wait_with_esc(wait_time):
    # Custom loop to replace core.wait() and check for Esc press
    start_time = core.getTime()
    while core.getTime() - start_time < wait_time:
        keys = event.getKeys()  # Get any key presses
        if 'escape' in keys:    # If 'Esc' key is pressed
            cleanup_parallel()
            core.quit()  # Quit PsychoPy

        core.wait(0.01)  		# Small wait to reduce CPU usage
    
## Create folders and logging files
# ensure that relative paths start from the same directory as this script
_thisDir = op.dirname(op.abspath(__file__))
os.chdir(_thisDir)
# create output folder for this subject and session and determine filename
filename = u'%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
output_path = _thisDir + os.sep + u'output/%s_%s_%s/%s' % (expInfo['participant'], expName, expInfo['date'],expInfo['session'])
if not resume_flag:
    os.makedirs(output_path, exist_ok=True)
# an ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, 
                                 version='',
                                 extraInfo=expInfo, 
                                 runtimeInfo=None,
                                 originPath= __file__,
                                 savePickle=True, saveWideText=True,
                                 dataFileName=op.join(output_path,'exp'))
# save a log file for detail verbose info
logFile = logging.LogFile(op.join(output_path, 'log.log'), level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

# === VOLUME Configuration ===
volume = 0.5             # Initial volume
step = 0.05              # Volume change step
min_vol, max_vol = 0.0, 1.0

# Replace with actual file paths or relative paths
speechtest_files = [
     os.path.join(volumetest_folder,'UvA0016.wav'),
     os.path.join(volumetest_folder,'UvA0019.wav'),
     os.path.join(volumetest_folder,'UvA0031.wav'),
     os.path.join(volumetest_folder,'UvA0035.wav'),
     os.path.join(volumetest_folder,'UvA0042.wav')
]
current_idx = 0

# === Setup Window ===
win = visual.Window(fullscr=False, color='black')
text = visual.TextStim(win, color='white', height=0.06)

# === Initial Instructions ===
instruction = visual.TextStim(win, text="Volume Setup\n\nUse UP/DOWN to adjust volume\nUse LEFT/RIGHT to play different phrases\nPress SPACE when comfortable", color='white', height=0.05, wrapWidth=1.6)
instruction.draw()
win.flip()
core.wait(3)

# === Calibration Loop ===
while True:
    phrase_name = os.path.basename(speechtest_files[current_idx])
    text.text = f"Volume: {volume:.2f}\nPhrase: {phrase_name}\n\nUse UP/DOWN to change volume\nLEFT/RIGHT to change phrase\nPress SPACE only to finally confirm"
    text.draw()
    win.flip()

    keys = event.getKeys()
    
    if 'up' in keys:
        volume = min(max_vol, volume + step)
        sound.Sound(speechtest_files[current_idx], volume=volume).play()
    elif 'down' in keys:
        volume = max(min_vol, volume - step)
        sound.Sound(speechtest_files[current_idx], volume=volume).play()
    elif 'right' in keys:
        current_idx = (current_idx + 1) % len(speechtest_files)
        sound.Sound(speechtest_files[current_idx], volume=volume).play()
    elif 'left' in keys:
        current_idx = (current_idx - 1) % len(speechtest_files)
        sound.Sound(speechtest_files[current_idx], volume=volume).play()
    elif 'space' in keys:
        break

    core.wait(0.1)  # to prevent CPU overload

# === Final Volume Ready ===
final_volume = volume
print(f"[INFO] Final volume set to: {final_volume:.2f}")
#Add to experiment data file
thisExp.addData('final_volume', final_volume)

run_params = {"continuous_record_after": record_after,
            "interval_cross_sound": interval_cross_sound,
            "volume": final_volume,
            "n_repeat": n_repeat,
            "interval_dur_rep": gap_time,
            "rep_interval_cross_sound": rep_interval_cross_sound,
            "test_mode": test_mode,
            "test_n_stimulus": test_n_stimulus,
            "n_breaks": n_breaks,
            "n_breaks_rep": n_breaks_rep, 
            "control_mode": control_mode,
            "continue_key": continue_key,
            "types": types,
            "stimulus_folder": input_folder}
# Save params to yaml in output folder
save_params_to_yaml(run_params, filename=op.join(output_path, 'params.yaml'))

## LOAD THE PREPARED STIMULUS FILES FOR MUSICAL WAKE -1 ##
#set the output paths for the prepared stimuli list
rating_xlsx_musicality1 = os.path.join(output_path, 'wake_rating.xlsx')
rating_xlsx_wake = os.path.join(output_path, 'wake_sns_rating.xlsx')
# for the pre-rating session
sound_list1 = pd.read_excel(rating_xlsx_musicality1, sheet_name='SoundList1')
file_list = sound_list1['sound']
sound_type = sound_list1['type']
# for the repetition session
sound_list_wake_b1 = pd.read_excel(rating_xlsx_wake, sheet_name='Wake_Block_1')
sound_list_wake_b2 = pd.read_excel(rating_xlsx_wake, sheet_name='Wake_Block_2')
file_list_w1 = sound_list_wake_b1['sound']
sound_type_w1 = sound_list_wake_b1['type']
file_list_w2 = sound_list_wake_b2['sound']
sound_type_w2 = sound_list_wake_b2['type']

print("Loaded sound_list1, sound_list_wake_b1 and sound_list_wake_b2 from file.")

## --- Define the stimulus list for each session --- ##
n_stimulus_1 = len(sound_list1)
n_stimulus_b1 = len(sound_list_wake_b1)
n_stimulus_b2 = len(sound_list_wake_b2)

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

######################
## --- Init slider --- ##
######################
# Slider Parameter
startClock = core.Clock()
slider_width=.5
slider_height=.1
slider_orientation=0
slider_ticks=[1,2,3,4]
slider_labels=['Strongly Speech-like','Speech-like','Song-like','Strongly Song-like']
sliding = 0
oldRating=-1
marker_colour_discrete='blue'
marker_colour_continuous='red'
marker_size=.1
sliderColour='LightGray'
error_slider_data_null = -99

# Initialize components for Routine "trial"
(win_width, win_height) = win.size
trialClock = core.Clock()
slider_shape_width = 0.5
slider_shape_height = 0.5
margin_ratio_horizontal = 1.1
slider_shape = visual.Rect(win=win, name='slider_shape',
    width= win_width*slider_shape_width*margin_ratio_horizontal, height=win_height*slider_shape_height, 
    ori=0, pos=(0, 0), lineWidth=1, lineColor=[0,0,0], lineColorSpace='rgb',
    fillColor=[0,0,0], fillColorSpace='rgb', opacity=1, depth=-2.0, interpolate=True, )

slider = visual.Slider(win=win, name='slider',
    size=(win_width*slider_width, slider_height*win_height/2), pos=(0, 0), 
    labels=slider_labels, ticks=slider_ticks, granularity=slider_granularity, 
    style=['rating'], color=sliderColour, flip=False, depth=-3)
# text_slider = visual.TextStim(win=win, name='text_slider', text=' ', 
#     pos=(0, -.45), height=0.06, wrapWidth=None, ori=0, color='white', depth=-4.0)
# text_data = visual.TextStim(win=win, name='text_data', text=' ', 
#     pos=(0, -.45), height=0.03, wrapWidth=None, ori=0, color='white', depth=-5.0)
Idx = 0
for label in slider.labelObjs:
    label.height = .03  # Or whatever size you want
    label.wrapWidth = .2
    label.text=slider_labels[Idx]
    Idx+=1
slider.marker.color=marker_colour_discrete
#-----------------------
# Welcome Instruction
#-----------------------
#Trigger to begin new instruction
if trigger:
    send_trigger(reset_trigger_code)

    core.wait(0.005)

    send_trigger(instruction_trigger)

    core.wait(0.005)
text = visual.TextStim(win=win, text="Welcome to our experiment!\
    \n\nDuring the experiment, you will listen to some speech excerpts and you will\
    \n be asked to rate how much each stimulus sounds as speech-like or song-like.\
    \n\n " + control_text +" to continue!",\
    color="white",
    contrast=contrast,
    wrapWidth=max(win.size)/ratio_text_width,
    height= max(win.size)/ratio_text_size)
text.autoDraw = True 
win.flip()
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
text.autoDraw = False    
win.flip()  

#-----------------------
# Trial Instruction
#-----------------------
n_sound = n_stimulus_1
if trigger:
    #Trigger to begin new instruction
    send_trigger(reset_trigger_code)

    core.wait(0.005)

    send_trigger(instruction_trigger)

    core.wait(0.005)
if not resume_flag:
    trial_instruct = "You will listen to " + str(n_sound) + " sound stimuli presented in " + str(n_blocks+1) + " blocks and within each block there will be " + str(n_breaks+1) + " breaks."\
        "\n\n For each stimulus, it will be played once, and you need to \
        \n rate how much it sounds speech-like or song-like by a slider.\
        \n\n Be sure to pay close attention to the sounds as they can be short.\
        \n\n" + control_text + " to continue!"
else:
    trial_instruct = "Welcome back!\
                       \n\n The experiment will resume from the interrupt point.\
                       \n\n " + control_text +" to continue!" 
text = visual.TextStim(win=win, text=trial_instruct,\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True 
win.flip()
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
text.autoDraw = False    
win.flip()  

#-----------------------
# Stimulus Presentation
#-----------------------
if test_mode:
    n_stimulus_for_loop = test_n_stimulus
else :
    n_stimulus_for_loop = n_stimulus_1

break_count = 0
n_stimulus_each_break = math.ceil( n_stimulus_for_loop / (n_breaks+1) )

if not resume_flag:
    # new experiment: loop all
    stimulus_array_for_loop = range(n_stimulus_for_loop)
else:
    # resume mode: loop from break point
    # find the break point
    # find the last rating
    rating_cols = [item for item in sound_list1.columns if 'rating' in item]

    last_valid_row = -1
    for col in rating_cols:
        last_valid_index_col = sound_list[col].last_valid_index()
        if last_valid_index_col is None:
            last_valid_index_col = -1
        last_valid_row = max(last_valid_row, last_valid_index_col)

    resume_sound_idx = last_valid_row + 1

    stimulus_array_for_loop = range(resume_sound_idx,n_stimulus_for_loop)

for sound_idx in stimulus_array_for_loop:
    cur_sound_name = sound_list1['sound'][sound_idx]
    cur_type = sound_list1['type'][sound_idx]
    cur_sound_path_1 = os.path.join(_thisDir, input_folder , cur_type, cur_sound_name) #individual stimuli
   
    mySound = sound.Sound(cur_sound_path_1, preBuffer=-1, volume=volume)
    # get sound duration
    duration = mySound.getDuration()
    sound_list1['duration'] [sound_idx] = duration
    write_value_to_excel(rating_xlsx_musicality1,'SoundList1',duration,cur_sound_name,'duration')

    #------------------------------
    # Block start
    #------------------------------
    if sound_idx == (break_count) * n_stimulus_each_break:
        text = visual.TextStim(win=win, text=" The No." + str(break_count+1) +" block starts soon."\
            "\n\n " + control_text + " to continue!",\
        color="white",
        contrast=contrast,\
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size)
        text.autoDraw = True 
        win.flip()
        if control_mode == 'key':
            wait_for_enter_key(end_key_name)
        elif control_mode == 'mouse':
            wait_for_mouse_click(mouse)
        text.autoDraw = False
    
    text = visual.TextStim(win=win, text="Excerpt No. " + str(sound_idx+1) + " is about to start."\
                           	"\n\n" + control_text + " to continue!",\
        color="white",
        contrast=contrast,
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size
        )
    text.autoDraw = True 
    win.flip()
    if control_mode == 'key':
        wait_for_enter_key(end_key_name)
    elif control_mode == 'mouse':
        wait_for_mouse_click(mouse)
    text.autoDraw = False    
    win.flip()  
    #-----------------------
    # pre-trial
    #-----------------------
    # show fixation
    fixation.autoDraw = True
    win.mouseVisible = False
    win.flip()

    # an interval before presentation
    core.wait(interval_cross_sound)

    # play sound
    if trigger:
        #Trigger to begin new instruction
        send_trigger(reset_trigger_code)

        core.wait(0.005)
        send_trigger(instruction_trigger)

        core.wait(0.005)
    play_sound(cur_sound_path_1, volume)
    fixation.autoDraw = False 
    win.flip()

    # rate the sound
    if control_mode == 'mouse':
        win.mouseVisible = True
    #-----------------------
    # pre-trial Rating
    #-----------------------
    slider.marker.color = marker_colour_discrete
    if control_mode == 'key':
        above_text_str = "Please move slider to rate the excerpt by '←' and '→'."\
            "\n\n " + control_text + " to continue!"
    elif control_mode == 'mouse':
        above_text_str = "Please move mouse to rate the excerpt."\
            "\n\n " + control_text + " to continue!"
    above_text = visual.TextStim(win=win, text=above_text_str,\
        color="white",pos=(0, 0.3*win.size[1]/2), contrast=contrast, wrapWidth=max(win.size)/ratio_text_width, height= max(win.size)/ratio_text_size)
    oldRating = -1
    if control_mode == 'key':
        _ , cur_pre_trial_slider_data = slider_routine_discrete_key(win, slider, slider_shape, 
                slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
                   slider_decimals, slideSpeed, oldRating, above_text, step_size, end_key_name)
    elif control_mode =='mouse':
        _ , cur_pre_trial_slider_data = slider_routine_discrete(win, slider, slider_shape, slider_orientation, 
                                                                    slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, 
                                                                    slideSpeed, oldRating, mouse, above_text)
    
    # get pre-trial rating and save    
    try:
        cur_pre_trial_rating = cur_pre_trial_slider_data[-1][0]
        oldRating = cur_pre_trial_rating
    except IndexError:
        cur_pre_trial_rating = error_slider_data_null
        oldRating = -1

    sound_list1['pre-rating'][sound_idx] = cur_pre_trial_rating
    write_value_to_excel(rating_xlsx_musicality1,'SoundList1',cur_pre_trial_rating,cur_sound_name,'pre-rating')
    core.wait(1)

    #-------------------------------
    # pre-trial Rating CONFIRMATION
    #-------------------------------
    slider.marker.color = marker_colour_discrete
    above_text = visual.TextStim(win=win, text="Please confirm your rating."\
                                 "\n\n " + control_text + " to continue!",
        color="white",pos=(0, 0.3*win.size[1]/2), contrast=contrast, wrapWidth=max(win.size)/ratio_text_width, height= max(win.size)/ratio_text_size)
    if control_mode == 'key':
        _ , cur_pre_trial_cfm_slider_data = slider_routine_discrete_key(win, slider, slider_shape, 
                slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
                   slider_decimals, slideSpeed, oldRating, above_text, step_size, end_key_name)
    elif control_mode == 'mouse':
        _ , cur_pre_trial_cfm_slider_data = slider_routine_discrete(win, slider, slider_shape, slider_orientation, 
                                                                    slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, 
                                                                    slideSpeed, oldRating, mouse, above_text)
    
    # get pre-trial rating and save
    try:
        cur_pre_trial_cfm_rating = cur_pre_trial_cfm_slider_data[-1][0]
    except IndexError:
        cur_pre_trial_cfm_rating = error_slider_data_null
        
    sound_list1['pre-rating_confirm'][sound_idx] = cur_pre_trial_cfm_rating
    write_value_to_excel(rating_xlsx_musicality1,'SoundList1',cur_pre_trial_cfm_rating,cur_sound_name,'pre-rating_confirm')

    #------------------------------
    # Break Time
    #------------------------------
    if sound_idx == (break_count+1) * n_stimulus_each_break - 1 :
        text = visual.TextStim(win=win, text=" Well done!  You finished Block No. " + str(break_count+1) + "! "\
            "\n\n You can take a short break."\
            "\n\n When you are ready, please " + control_text + " to continue!",\
        color="white",
        contrast=contrast,\
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size)
        text.autoDraw = True 
        win.flip()
        if control_mode == 'key':
            wait_for_enter_key(end_key_name)
        elif control_mode == 'mouse':
            wait_for_mouse_click(mouse)
        text.autoDraw = False
        break_count += 1

#-----------------------
# Ending of Wake Musicality Rating 1 
#-----------------------
text = visual.TextStim(win=win, text="Congratulations! You finished all excerpts for the first session in this phase!"\
                       "\n\n You can take a break now."\
                       "\n\n Please hit continue when you are ready to enter into the next phase of this experiment :)",\
    color="white",
    contrast=contrast,\
    wrapWidth=max(win.size)/ratio_text_width,
    height= max(win.size)/ratio_text_size)
text.autoDraw = True 
win.flip()
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
text.autoDraw = False

# Session Two: Wake Speech2Song Illusion with repeated stimuli
#----------------------------
# trial (stimulus repetition)
#----------------------------
# load correct Stimulus set for wake blocks
try:
    # Check if variables exist in the current workspace
    sound_list_wake_b1
    sound_list_wake_b2
    n_stimulus_b1
    n_stimulus_b2
    print("Loaded sound_list_wake_b1 and sound_list_wake_b2 from workspace.")
    file_list_w1 = sound_list_wake_b1['sound']
    sound_type_w1 = sound_list_wake_b1['type']
    file_list_w2 = sound_list_wake_b2['sound']
    sound_type_w2 = sound_list_wake_b2['type']
except NameError:
    # Fallback: Load from the existing directory if variables are not defined
    print("sound_list_wake_b1 and/or sound_list_wake_b2 not found in workspace. Loading from file...")
    sound_list_wake_b1 = pd.read_excel(rating_xlsx_wake, sheet_name='Wake_Block_1')
    sound_list_wake_b2 = pd.read_excel(rating_xlsx_wake, sheet_name='Wake_Block_2')
    n_stimulus_b1 = len(sound_list_wake_b1)
    n_stimulus_b2 = len(sound_list_wake_b2)
    file_list_w1 = sound_list_wake_b1['sound']
    sound_type_w1 = sound_list_wake_b1['type']
    file_list_w2 = sound_list_wake_b2['sound']
    sound_type_w2 = sound_list_wake_b2['type']
    print("Loaded sound_list_wake_b1 and sound_list_wake_b2 from file.")
    
    
# Trial Instruction
#-----------------------
# initialise the block specific sound lists for Wake SnS session
blocks = [
    {"name": "Wake_Block_1", "sound_list": sound_list_wake_b1},
    {"name": "Wake_Block_2", "sound_list": sound_list_wake_b2},
]

text = visual.TextStim(win=win, text="Welcome to the second session of the wake phase! "\
                       "\n\n Please hit continue when you are ready to enter into the next phase :)",\
    color="white",
    contrast=contrast,\
    wrapWidth=max(win.size)/ratio_text_width,
    height= max(win.size)/ratio_text_size)
text.autoDraw = True 
win.flip()
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
text.autoDraw = False
print("works here 1.")
# Block-wise trials

#-----------------------
# Stimulus Presentation
#-----------------------

test_n_stimulus = 4
if test_mode:
    n_stimulus_for_loop = test_n_stimulus
else :
    n_stimulus_for_loop = n_stimulus_b1


n_sound_b1 = n_stimulus_b1
n_sound_b2 = n_stimulus_b2
break_count = 2
n_stimulus_each_break = math.ceil( n_stimulus_for_loop / (n_breaks_rep+1) )
print("works here 2.")

# Block start
#------------------------------
# Trial (stimulus repetition)
#----------------------------
# Loop through blocks
for block_idx, block in enumerate(blocks):
    block_name = block["name"]
    sound_list_block = block["sound_list"]
    # Check if resuming and identify where to start
    if not resume_flag:
        stimulus_array_for_loop = range(len(sound_list_block))
    else:
        # Find the last saved rating and determine where to resume
        rating_cols = [col for col in sound_list_block.columns if 'rating' in col]
        last_valid_row = -1

        for col in rating_cols:
            last_valid_index = sound_list_block[col].last_valid_index()
            if last_valid_index is not None:
                last_valid_row = max(last_valid_row, last_valid_index)
        
        resume_sound_idx = last_valid_row + 1
        stimulus_array_for_loop = range(resume_sound_idx, len(sound_list_block))
    if control_mode == 'key':
        above_text_str_continuous ="You will listen to " + str(len(sound_list_block)) + " speech excerpts presented in this block "\
            "\n\n First, you will hear an excerpt and asked to rate its musicality. Then, the excerpt will be repeated " + str(n_repeat) + " times. You can\
            \n change your rating during the repetition when you feel changes in perception.\
            \n\n " + control_text + " to continue!"
    elif control_mode == 'mouse':
        above_text_str_continuous = "You will listen to " + str(len(sound_list_block)) + " speech excerpts presented in this block "\
            "\n\n First, you will hear an excerpt and asked to rate its musicality. Then, the excerpt will be repeated " + str(n_repeat) + " times. You can\
            \n change your rating during the repetition when you feel changes in perception.\
            \n\n " + control_text + " to continue!"
    text = visual.TextStim(win=win, text=above_text_str_continuous,\
    color="white",
    contrast=contrast,\
    wrapWidth=max(win.size)/ratio_text_width,
    height=max(win.size)/ratio_text_size)
    text.autoDraw = True 
    win.flip()
    if control_mode == 'key':
        wait_for_enter_key(end_key_name)
    elif control_mode == 'mouse':
        wait_for_mouse_click(mouse)
    text.autoDraw = False    
    win.flip()  
    

    # Loop through the stimuli in the block
    for sound_idx in stimulus_array_for_loop:
        cur_sound_name = sound_list_block['sound'][sound_idx]
        cur_type = sound_list_block['type'][sound_idx]
        cur_sound_path = os.path.join(_thisDir,input_folder, cur_type, cur_sound_name) #looped stimuli
        # Load the sound
        mySound = sound.Sound(cur_sound_path, preBuffer=-1, volume=volume)
        # get sound duration
        core_wait_with_esc(mySound.getDuration()+0.1)
        #sound_list_block['duration'][sound_idx] = mySound.getDuration()
        # pre-trial
        #-----------------------
        # Display information about the current stimulus
        text = visual.TextStim(win=win, text="Excerpt No. " + str(sound_idx+1) + " is about to start."\
                                "\n\n" + control_text + " to continue!",\
            color="white",
            contrast=contrast,
            wrapWidth=max(win.size)/ratio_text_width,
            height=max(win.size)/ratio_text_size)
        text.autoDraw = True 
        win.flip()
        if control_mode == 'key':
            wait_for_enter_key(end_key_name)
        elif control_mode == 'mouse':
            wait_for_mouse_click(mouse)
        text.autoDraw = False    
        win.flip()  
        # pre-trial
        #-----------------------
        # show fixation
        fixation.autoDraw = True
        win.mouseVisible = False
        win.flip()

        # an interval before presentation
        core.wait(interval_cross_sound)
        if trigger:
            #adding my specific triggers if needed
            send_trigger(reset_trigger_code)

            core.wait(0.005)
            send_trigger(song_trigger)
            print(f"Sending instruction trigger: {song_trigger}")
        # play sound
        stim_start_time = core.getTime()
        mySound.play()
        print(f"Sent song trigger at {stim_start_time:.3f} for {cur_sound_name}")
        #play_sound(cur_sound_path_1, volume)
        fixation.autoDraw = False 
        win.flip()

        # rate the sound
        if control_mode == 'mouse':
            win.mouseVisible = True
        #-----------------------
        # pre-trial Rating
        #-----------------------
        oldRating = -1
        slider.marker.color = marker_colour_discrete
        if control_mode == 'key':
            above_text_str = "Please move slider to rate the excerpt by '←' and '→'."\
                "\n\n " + control_text + " to continue!"
        elif control_mode == 'mouse':
            above_text_str = "Please move mouse to rate the excerpt."\
                "\n\n " + control_text + " to continue!"
        above_text = visual.TextStim(win=win, text=above_text_str,\
            color="white",pos=(0, 0.3*win.size[1]/2), contrast=contrast, wrapWidth=max(win.size)/ratio_text_width, height= max(win.size)/ratio_text_size)
        if control_mode == 'key':
            _ , cur_pre_trial_slider_data = slider_routine_discrete_key(win, slider, slider_shape, 
                    slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
                       slider_decimals, slideSpeed, oldRating, above_text, step_size, end_key_name)
        elif control_mode =='mouse':
            _ , cur_pre_trial_slider_data = slider_routine_discrete(win, slider, slider_shape, slider_orientation, 
                                                                        slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, 
                                                                        slideSpeed, oldRating, mouse, above_text)
        
        # get pre-trial rating and save    
        try:
            cur_pre_trial_rating = cur_pre_trial_slider_data[-1][0]
            oldRating = cur_pre_trial_rating
        except IndexError:
            cur_pre_trial_rating = error_slider_data_null
            oldRating = -1

        sound_list_block['pre-rating-rep'][sound_idx] = cur_pre_trial_rating
        #write_value_to_excel(file_path=rating_xlsx_wake,
         #sheet_name=block_name,
          #      column_name='pre-rating',
           #     value=oldRating,
            #    row_name=cur_sound_name
            #)
        write_value_to_excel(rating_xlsx_wake,block_name,cur_pre_trial_rating,cur_sound_name,'pre-rating-rep')

        

        if control_mode == 'key':
                wait_for_enter_key(end_key_name)
        elif control_mode == 'mouse':
                wait_for_mouse_click(mouse)
        text.autoDraw = False    
        win.flip()          
        # an interval before presentation
        core.wait(interval_cross_sound)
       # mySound.play()
            #core.wait(mySound.getDuration())

        # set start position of mouse and marker
        initial_marker_pos = cur_pre_trial_rating if not cur_pre_trial_rating == error_slider_data_null else (slider_ticks[0] + slider_ticks[-1])/2
        oldRating = initial_marker_pos
        initial_rel_mouse_pos = [((initial_marker_pos-(slider_ticks[0] + slider_ticks[-1])/2) / (slider_ticks[-1] - slider_ticks[0])*2),0]
        initial_mouse_pos = [0,0]
        initial_mouse_pos[slider_orientation] = initial_rel_mouse_pos[slider_orientation] * slider_shape_width /2 * win.size[slider_orientation]

        slider.marker.color = marker_colour_continuous
        if control_mode == 'key':
            above_test_str = " Remember that you can\
                \n change your rating during the repetition when you feel changes in perception.\
                \n\n At the time of change, adjust the rating using ← and → keys."\
                "\n\n If you do not feel any changes, then you do not need to do anything."

            cur_trial_slider, cur_trial_slider_data = slider_routine_continuous_key(
                win, slider, slider_shape, slider_orientation, slider_ticks,
                slider_granularity, slider_shape_width, slider_decimals, sliding,
                slideSpeed, oldRating,
                cur_sound_path.replace('stimuli', 'rep_concatenated_' + str(n_repeat) + 'times'),
                1, record_after, rep_interval_cross_sound, gap_time, volume, step_size
             )
            above_text = visual.TextStim(win=win, text=above_text_str,\
                color="white",pos=(0, 0.3*win.size[1]/2), contrast=contrast, wrapWidth=max(win.size)/ratio_text_width, height= max(win.size)/ratio_text_size)
            above_text.text = above_text_str
        elif control_mode == 'mouse':
            above_test_str = " Remember that you can\
                \n change your rating during the repetition when you feel changes in perception.\
                \n\n At the time of change, move the mouse to choose the rating on the slider."\
                "\n\n If you do not feel any changes, then you do not need to do anything."
            cur_trial_slider, cur_trial_slider_data = slider_routine_continuous(
                win, slider, slider_shape, slider_orientation, slider_ticks,
                slider_granularity, slider_shape_width, slider_decimals, sliding,
                slideSpeed, oldRating, mouse,
                cur_sound_path.replace('stimuli', 'rep_concatenated_' + str(n_repeat) + 'times'),
                1, record_after, rep_interval_cross_sound, gap_time, initial_mouse_pos,
                initial_marker_pos, volume
            )
        

        ratings = [item[0] for item in cur_trial_slider_data if item[1] >= rep_interval_cross_sound*1000]
        ratings = [cur_sound_name] + ratings
        times = [item[1] - rep_interval_cross_sound*1000 for item in cur_trial_slider_data if item[1] >= rep_interval_cross_sound*1000]
        times = [cur_sound_name] + times
        # Extract the first rating and time
        if cur_trial_slider_data:
            last_rating = cur_trial_slider_data[-1][0]  # First rating value
            last_time = cur_trial_slider_data[-1][1]   # Corresponding timestamp
        else:
            last_rating = None
            last_time = None

        # Save trial ratings
        ratings = [item[0] for item in cur_trial_slider_data]
        times = [item[1] for item in cur_trial_slider_data]
         # Save the first rating into the appropriate data structures
        sound_list_block['rep-rating'][sound_idx] = last_rating
        sound_list_block['time'][sound_idx] = last_time
        
        # Trial phase: Repetition
        #write_value_to_excel(
         #   file_path=rating_xlsx_wake,
          #  sheet_name=block_name,
           # column_name='rep-rating',
            #value=last_rating,
            #row_name=cur_sound_name
        #)
        write_value_to_excel(rating_xlsx_wake,block_name,last_rating,cur_sound_name,'rep-rating')

        #write_value_to_excel(
         #   file_path=rating_xlsx_wake,
         #sheet_name=block_name,
         #   column_name='time',
         #   value=last_time,
         #   row_name=cur_sound_name
        #)
        write_value_to_excel(rating_xlsx_wake,block_name,last_time,cur_sound_name,'time')
        # Post-rating phase
        
        slider.marker.color = marker_colour_discrete
        initial_marker_pos = last_rating if last_rating is not None else (slider_ticks[0] + slider_ticks[-1]) / 2
        oldRating = initial_marker_pos
        above_text.text = "Please confirm your final rating for this excerpt."
        _, cur_post_trial_slider_data = slider_routine_discrete_key(
            win, slider, slider_shape, slider_orientation, slider_ticks,
            slider_granularity, slider_shape_width, slider_decimals, slideSpeed,
            oldRating, above_text, step_size, continue_key)

        # Save post-rating
        try:
            cur_post_trial_rating = cur_post_trial_slider_data[-1][0]
        except IndexError:
            cur_post_trial_rating = error_slider_data_null

        #write_value_to_excel(
         #   file_path=rating_xlsx_wake,
         #sheet_name=block_name,
         #   column_name='rep-rating-confirm',
         #   value=cur_post_trial_rating,
         #   row_name=cur_sound_name
        #)
        write_value_to_excel(rating_xlsx_wake,block_name,cur_post_trial_rating,cur_sound_name,'rep-rating-confirm')
        # Break if needed
        if sound_idx % n_stimulus_each_break == 0 and sound_idx != 0:
            text = visual.TextStim(win=win, text="Take a short break."\
                "\n\n Press Enter to continue.",
                color="white", wrapWidth=max(win.size) / ratio_text_width,
                height=max(win.size) / ratio_text_size)
            text.autoDraw = True
            win.flip()
            wait_for_enter_key(continue_key)
            text.autoDraw = False
            win.flip()
    # End of Block text
    #-----------------------
    if block_idx < len(blocks) - 1:
         text = visual.TextStim(
             win=win, text="Great work! You have completed block no. " + str(block_idx + 1) + " of this session!" \
                "\n\n You can take a break now." \
                "\n\n Please hit continue when you are ready to enter into the next block :)",
              color="white",
              contrast=contrast,
              wrapWidth=max(win.size) / ratio_text_width,
              height=max(win.size) / ratio_text_size
            )
         text.autoDraw = True
         win.flip()

    if control_mode == 'key':
         wait_for_enter_key(end_key_name)
    elif control_mode == 'mouse':
         wait_for_mouse_click(mouse)
            
    text.autoDraw = False
    win.flip()


#------------------------
# END
#------------------------
text = visual.TextStim(win=win, text="Congratulations! You finished all excerpts!"\
                       "\n\n Please wait for your experimenter. :)",\
    color="white",
    contrast=contrast,\
    wrapWidth=max(win.size)/ratio_text_width,
    height= max(win.size)/ratio_text_size)
text.autoDraw = True 
win.flip()
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)
text.autoDraw = False
win.close()