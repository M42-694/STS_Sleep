# --- Import packages ---
from numpy.random import random
import pandas as pd
import numpy as np
import os 
import random
import math
import os.path as op
import serial
import atexit

from psychopy import prefs
from psychopy import plugins
from psychopy import sound, gui, visual, core, data, event, logging
from psychopy import core, event, sound

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
input_folder = 'input_new/stimuli/'
input_rep_folder = 'input_new/rep_concatenated_8times'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
# debug
resume_flag = False
test_mode = True
test_n_stimulus = 2
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
port_name = 'COM6'
#trigger codes
reset_trigger_code = b'\x00'
start_session = b'\x15'
stop_session = b'\x63'

instruction_trigger = b'\x37'  # for all instruction slides
song_trigger = b'\x0B'         # for all audio stimuli

import serial.tools.list_ports
ports=serial.tools.list_ports.comports()
for port,desc,hwid in ports:
    print(f"Port: {port}, Description: {desc},HWID:{hwid}")
    
run_params = {"continuous_record_after": record_after,
            "interval_cross_sound": interval_cross_sound,
            "volume": volume,
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
        
def core_wait_with_esc(wait_time):
    start_time = core.getTime()
    while core.getTime() - start_time < wait_time:
        keys = event.getKeys()
        if 'escape' in keys:
            print("ESC pressed. Cleaning up and exiting...")

            # Safely close serial port if it exists
            try:
                if 'SerialPortObj' in globals() and SerialPortObj.is_open:
                    SerialPortObj.close()
                    print("Serial port closed successfully.")
            except Exception as e:
                print(f"Failed to close serial port: {e}")

            # Safely terminate audio backend if using PTB
            try:
                sound.backend_ptb.audioLib._terminate()
                print("PTB audio backend terminated successfully.")
            except Exception as e:
                print(f"Failed to terminate PTB audio backend: {e}")

            core.quit()  # Quit PsychoPy safely after cleanup

        core.wait(0.01)  # Small wait to reduce CPU usage

if trigger:
    # select here the address of your port
    setup_serial()
## Create folders and logging files
# ensure that relative paths start from the same directory as this script
_thisDir = op.dirname(op.abspath(__file__))
os.chdir(_thisDir)
# create output folder for this subject and session and determine filename
filename = u'%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
output_path = _thisDir + os.sep + u'output/%s_%s_%s/%s' % (expInfo['participant'], expName, expInfo['date'],expInfo['session'])
if not resume_flag:
    os.makedirs(output_path, exist_ok=False)
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

# Save params to yaml in output folder
save_params_to_yaml(run_params, filename=op.join(output_path, 'params.yaml'))

# --- Prepare sub groups of Sound Sequences ---
def Split_Stimuli(sound_list, group_names=["Wake", "Nap", "New"]):
    """
    Split stimuli into three parts and assign groups.

    Parameters:
        sound_list (pd.DataFrame): DataFrame containing sound files and their types.
        group_names (list): List of group names to assign (default: ["Wake", "Nap", "New"]).

    Returns:
        pd.DataFrame: DataFrame with assigned groups.
    """
    # Separate into Speech and Song
    speech_stimuli = sound_list[sound_list['type'] == "speech"]
    song_stimuli = sound_list[sound_list['type'] == "song"]
    # Debugging print statements
    print(f"Number of speech stimuli: {len(speech_stimuli)}")
    print(f"Number of song stimuli: {len(song_stimuli)}")
    
    # Ensure there are exactly 24 stimuli per type
    assert len(speech_stimuli) == 24, f"There must be exactly 24 speech stimuli. Now there is {len(speech_stimuli)}"
    assert len(song_stimuli) == 24, f"There must be exactly 24 song stimuli. Now there is {len(song_stimuli)}"
    
    # Shuffle stimuli
    speech_stimuli = speech_stimuli.sample(frac=1).reset_index(drop=True)
    song_stimuli = song_stimuli.sample(frac=1).reset_index(drop=True)
    
    # Split into groups (8 per group)
    group_sizes = len(group_names)
    speech_groups = [speech_stimuli.iloc[i::group_sizes] for i in range(group_sizes)]
    song_groups = [song_stimuli.iloc[i::group_sizes] for i in range(group_sizes)]

   
    # Assign groups
    for i, group_name in enumerate(group_names):
         speech_groups[i].loc[:, "stim_group"] = group_name
         song_groups[i].loc[:, "stim_group"] = group_name
    # Combine groups
    sound_list= pd.concat(speech_groups + song_groups, ignore_index=True)
    return sound_list
    
#assign output filenames for stimulus groups and ratings
rating_xlsx_musicality1 = op.join(output_path, 'wake_rating.xlsx')
rating_xlsx_musicality2= op.join(output_path,'post_nap_rating.xlsx')
rating_xlsx_wake = op.join(output_path,'wake_sns_rating.xlsx')
play_xlsx_nap = op.join(output_path,'nap_sns_list.xlsx')

#Randomize the original stimulus list
def StimulusSeqInit(stimulus_list):
    ''' randomize stimulus sequence '''
    ''' modern Fisher–Yates shuffle '''
    n_stimulus = len(stimulus_list)
    ran_order = list(tuple(range(n_stimulus)))
    random.shuffle(ran_order)     
    ran_stimulus_list = stimulus_list.reindex(index=ran_order)
    ran_stimulus_list.reset_index(drop=True, inplace=True)
    return ran_stimulus_list    
    
if not resume_flag:
    # create sound list from main stimuli list
    main_list, sound_type = [], []
    for type in types:
        # Filter the file list to include only .wav files
        cur_file_list = [
            f for f in os.listdir(os.path.join(input_folder, type))
            if f.endswith('.wav')
        ]

        main_list = main_list + cur_file_list
        
        sound_type = sound_type + [type] * len(cur_file_list)
    

    sound_list = pd.DataFrame({'sound': main_list, 'type': sound_type})
    print(f"Number of total stimuli: {len(sound_list)}")
    #assert len(sound_list) == 48, f"There must be exactly 48 stimuli. Now there is {len(sound_list)} }"
    #Create the meta list with Group_Names for full experiment
    sound_list0 = Split_Stimuli(sound_list)
    # Shuffle the list to create a Sound List for Musicality Rating
    sound_list1 = StimulusSeqInit(sound_list0)
    #Shuffle soundlist1 again to have a new main sound list for post-nap Musicality Rating
    sound_list2 = StimulusSeqInit(sound_list0) 
    #Extract groups based on Stimulus Group Wake and Nap
    def assign_blocks(sound_list, group_name, block_count, random_states):
        return [
        sound_list[sound_list["stim_group"] == group_name].sample(frac=1, random_state=state).reset_index(drop=True)
        for state in random_states[:block_count]
    ]
    random_states_wake = [42, 43]
    random_states_nap = [44, 45, 46]
    sound_list_wake_blocks = assign_blocks(sound_list0, 'Wake', 2, random_states_wake)
    sound_list_nap_blocks = assign_blocks(sound_list0, 'Nap', 3, random_states_nap)

    # Access blocks
    sound_list_wake_b1 = sound_list_wake_blocks[0]
    sound_list_wake_b2 = sound_list_wake_blocks[1]
    sound_list_wake_b1['block'] = 'Wake Block 1'
    sound_list_wake_b2['block'] = 'Wake Block 2'

    sound_list_nap_b1 = sound_list_nap_blocks[0]
    sound_list_nap_b2 = sound_list_nap_blocks[1]
    sound_list_nap_b3 = sound_list_nap_blocks[2]
    sound_list_nap_b1['block'] = 'Nap Block 1'
    sound_list_nap_b2['block'] = 'Nap Block 2'
    sound_list_nap_b3['block'] = 'Nap Block 3'
        
    # add properties of sound_list_nap and sound_list_wake
    sound_list_wake_b1['rep-rating'] = None
    sound_list_wake_b1['time'] = None
    sound_list_wake_b1['rep-rating-confirm'] = None
    sound_list_wake_b2['rep-rating'] = None
    sound_list_wake_b2['time'] = None
    sound_list_wake_b2['rep-rating-confirm'] = None
    '''Nap blocks dont have rating recording'''

    # add properties of soundlist1
    sound_list1['duration'] = None
    sound_list1['pre-rating'] = None
    sound_list1['pre-rating_confirm'] = None
    # add properties of soundlist1
    sound_list2['duration'] = None
    sound_list2['post-rating'] = None
    sound_list2['post-rating_confirm'] = None
    sound_list2['memory'] = None

    # save all sound lists to excel
    with pd.ExcelWriter(rating_xlsx_musicality1 ) as writer:
        sound_list1.to_excel(writer, sheet_name='SoundList1')
    with pd.ExcelWriter(rating_xlsx_musicality2) as writer:
        sound_list2.to_excel(writer, sheet_name = 'SoundList2')
        
    with pd.ExcelWriter(rating_xlsx_wake ) as writer:
        sound_list_wake_b1.to_excel(writer, sheet_name='Wake_Block_1', index=False)
        sound_list_wake_b2.to_excel(writer, sheet_name='Wake_Block_2', index=False)

    with pd.ExcelWriter(play_xlsx_nap) as writer:
        sound_list_nap_b1.to_excel(writer, sheet_name='Nap_Block_1', index=False)
        sound_list_nap_b2.to_excel(writer, sheet_name='Nap_Block_2', index=False)
        sound_list_nap_b3.to_excel(writer, sheet_name='Nap_Block_3', index=False)
    # read sound list
    sound_list1 = pd.read_excel(rating_xlsx_musicality1, sheet_name='SoundList1')
    file_list = sound_list1['sound']
    sound_type = sound_list1['type']
 
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
SerialPortObj.write(reset_trigger_code)
#SerialPortObj.flush()
core.wait(0.005)

SerialPortObj.write(instruction_trigger)
#SerialPortObj.flush()
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
#Trigger to begin new instruction
SerialPortObj.write(reset_trigger_code)
#SerialPortObj.flush()
core.wait(0.005)

SerialPortObj.write(instruction_trigger)
#SerialPortObj.flush()
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
    #adjust volume of the audio
    # Check for volume control keys before each sound
    keys = event.getKeys()
    if 'up' in keys:
        volume = min(volume + 0.1, 1.0)  # Increase volume, cap at 1.0
    if 'down' in keys:
        volume = max(volume - 0.1, 0.0)  # Decrease volume, floor at 0.0

    print(f"Current volume: {volume}")
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
    #Trigger to begin new instruction
    SerialPortObj.write(reset_trigger_code)
    #SerialPortObj.flush()
    core.wait(0.005)
    SerialPortObj.write(instruction_trigger)
    #SerialPortObj.flush()
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
        #adjust volume of the audio
        # Check for volume control keys before each sound
        keys = event.getKeys()
        if 'up' in keys:
            volume = min(volume + 0.1, 1.0)  # Increase volume, cap at 1.0
        if 'down' in keys:
            volume = max(volume - 0.1, 0.0)  # Decrease volume, floor at 0.0

        print(f"Current volume: {volume}")
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

        #adding my specific triggers if needed
        SerialPortObj.write(reset_trigger_code)
        #SerialPortObj.flush()
        core.wait(0.005)
        SerialPortObj.write(song_trigger)
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

        sound_list_block['pre-rating'][sound_idx] = cur_pre_trial_rating
        write_value_to_excel(file_path=rating_xlsx_wake,
                sheet_name=block_name,
                column_name='pre-rating',
                value=oldRating,
                row_name=cur_sound_name
            )
        

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
        # Save to Excel
        write_value_to_excel(file_path=rating_xlsx_wake,
            sheet_name=block_name,
            column_name='duration',
            value=mySound.duration,
            row_name=cur_sound_name
        )
        # Trial phase: Repetition
        write_value_to_excel(
            file_path=rating_xlsx_wake,
            sheet_name=block_name,
            column_name='rep-rating',
            value=last_rating,
            row_name=cur_sound_name
        )
        
        write_value_to_excel(
            file_path=rating_xlsx_wake,
            sheet_name=block_name,
            column_name='time',
            value=last_time,
            row_name=cur_sound_name
        )
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

        write_value_to_excel(
            file_path=rating_xlsx_wake,
            sheet_name=block_name,
            column_name='rep-rating-confirm',
            value=cur_post_trial_rating,
            row_name=cur_sound_name
        )
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