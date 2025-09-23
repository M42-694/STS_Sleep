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

plugins.activatePlugins()
prefs.hardware['audioLib'] = ['PTB'] #['sounddevice', 'PTB', 'pyo', 'pygame'] #'ptb' ['PTB']
prefs.hardware['audioDevice'] = 'Scarlett Solo USB'  
prefs.hardware['sampleRate'] = 44100 
prefs.hardware['audioLatencyMode'] = '0'
defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')

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

################################
# --- Parameter to control --- #
################################
# param exp
psychopyVersion = '2024.2.4'
expName = 'speech2song'
input_folder = 'input/stimuli/'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
# debug
resume_flag = False
test_mode = True
test_n_stimulus = 2
# sound presentation
volume = 1
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
slideSpeed = 70*slider_granularity

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

## Create folders and logging files
# ensure that relative paths start from the same directory as this script
_thisDir = op.dirname(op.abspath(__file__))
os.chdir(_thisDir)
# create output folder for this subject and session and determine filename
filename = u'%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
output_path = _thisDir + os.sep + u'output/%s_%s_%s/%s' % (expInfo['participant'], expName, expInfo['date'],expInfo['session'])
image_path = _thisDir + os.sep + 'responsegrid_image.png'
if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image file not found: {image_path}")
if not resume_flag and not os.path.exists(output_path):
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

# Save params to yaml in output folder
save_params_to_yaml(run_params, filename=op.join(output_path, 'params.yaml'))

# read sound list
rating_xlsx_musicality2= op.join(output_path,'post_nap_rating.xlsx')
sound_list2 = pd.read_excel(rating_xlsx_musicality2, sheet_name='SoundList2')
file_list = sound_list2['sound']
sound_type = sound_list2['type']
 
## --- Define the stimulus list for each session --- ##
n_stimulus = len(sound_list2)

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
Idx = 0
for label in slider.labelObjs:
    label.height = .03  # adjust label size here
    label.wrapWidth = .2 #to prevent overflowing 
    label.text=slider_labels[Idx]
    Idx+=1
slider.marker.color=marker_colour_discrete
#-----------------------
# Welcome Instruction
#-----------------------
text = visual.TextStim(win=win, text="Welcome to our experiment!\
    \n\nDuring the last phase of today's experiment, you will listen to some speech excerpts. Once again, you will\
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
n_sound = n_stimulus
if not resume_flag:
    trial_instruct = "You will listen to " + str(n_sound) + " sound stimuli presented in " + str(n_blocks+1) + " blocks and within each block there will be " + str(n_breaks+1) + " breaks."\
        "\n\n For each stimulus, it will be played once, and you need to \
        \n rate how much it sounds speech-like or song-like by a slider.\
        \n\n Be sure to pay close attention to the sounds as they can be short.\
        \n\n" + control_text + " to continue!"
    trial_instruct2="You will also be asked if you recall the excerpt from previous presentations, \n either before or during the nap. \n\n" + control_text + " to continue!"  
    trial_instruct3="At the same time, you will be asked to rate on your confidence: \n\n1. (I am not sure at all / uncertain) to 4 (I am very sure / certain. \n\n" + control_text + " to continue."

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

# --- Initialize components for Routine "memory_instructions" ---
text = visual.TextStim(win=win, text="You will also be asked if you recall the excerpt from previous presentations, \n either before or during the nap. \n\n Press any key to continue!" , \
        contrast=contrast,color='white',
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size)
text.autoDraw = True 
win.flip()
event.waitKeys()
text.autoDraw = False    
win.flip()  
# --- Initialize components for Routine "mem_insturc_1" ---
text = visual.TextStim(win=win, text ="At the same time, you will be asked to rate on your confidence: \n\n1. (I am not sure at all / uncertain) to 4 (I am very sure / certain. \n\n Press any key to continue." ,\
        contrast=contrast, color='white',
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False
win.flip()
    
# --- Initialize components for Routine "mem_instruc_2" ---
respgridimage = visual.ImageStim(
        win=win, 
        image=image_path,
        ori=0.0, pos=(0, 0), size=(0.7, 0.7),
        color=[1, 1, 1], colorSpace='rgb', opacity=1.0,
        flipHoriz=False, flipVert=False,
        texRes=128, interpolate=True, depth=0.0)
respgridpost_continue = visual.TextStim(win=win, name='respgridpost_continue',\
        text= control_text + " to continue",
        contrast=contrast, color='white',
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size)
respgridimage.draw()
core.wait(5)
respgridpost_continue.autoDraw = True

win.flip()
event.waitKeys()

respgridpost_continue.autoDraw = False

win.flip()

# --- Initialize components for Routine "expl_respgrid" ---
expl_respscreen_text = visual.TextStim(win=win, name='trial_instruc4',
        text="Example:\n\n- Click on 4 to the right if you heard the excerpt before the nap. \n\n Hit " + control_text + " to continue",
        contrast=contrast, color='white',
        wrapWidth=max(win.size)/ratio_text_width,
        height= max(win.size)/ratio_text_size)
expl_respscreen_text.autoDraw = True
win.flip()
if control_mode == 'key':
    wait_for_enter_key(end_key_name)
elif control_mode == 'mouse':
    wait_for_mouse_click(mouse)

expl_respscreen_text.autoDraw = False
win.flip()
# --- Initialize components for Routine "memory_old_new" ---

wake_1 = visual.ShapeStim(
        win=win, name='wake_1',
        size=(0.4, 0.2), vertices='triangle',
        ori=225.0, pos=(0.0975, -0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000,1.0000,1.0000],
        opacity=None, depth=-1.0, interpolate=True)
wake_2 = visual.ShapeStim(
        win=win, name='wake_2',
        size=(0.4, 0.2), vertices='triangle',
        ori=45.0, pos=(0.25, -0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000,1.0000,1.0000],
        opacity=None, depth=-2.0, interpolate=True)
wake_3 = visual.ShapeStim(
        win=win, name='wake_3',
        size=(0.4, 0.2), vertices='triangle',
        ori=135.0, pos=(0.25, 0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-3.0, interpolate=True)
wake_4 = visual.ShapeStim(
        win=win, name='wake_4',
        size=(0.4, 0.2), vertices='triangle',
        ori=315.0, pos=(0.0975, 0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-4.0, interpolate=True)
nap_4 = visual.ShapeStim(
        win=win, name='nap_4',
        size=(0.4, 0.2), vertices='triangle',
        ori=45.0, pos=(-0.0975, 0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-5.0, interpolate=True)
nap_3 = visual.ShapeStim(
        win=win, name='nap_3',
        size=(0.4, 0.2), vertices='triangle',
        ori=225.0, pos=(-0.25, 0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-6.0, interpolate=True)
nap_2 = visual.ShapeStim(
        win=win, name='nap_2',
        size=(0.4, 0.2), vertices='triangle',
        ori=315.0, pos=(-0.25, -0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-7.0, interpolate=True)
nap_1 = visual.ShapeStim(
        win=win, name='nap_1',
        size=(0.4, 0.2), vertices='triangle',
        ori=135.0, pos=(-0.0975, -0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-8.0, interpolate=True)
line = visual.Line(
        win=win, name='line',
        start=(-(0.575, 0.575)[0]/2.0, 0), end=(+(0.575, 0.575)[0]/2.0, 0),
        ori=0.0, pos=(0, 0), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[-1.0000, -1.0000, -1.0000], fillColor=[-1.0000, -1.0000, -1.0000],
        opacity=None, depth=-10.0, interpolate=True)
text_Wake = visual.TextStim(win=win, name='text_Wake',
        text='W\nA\nK\nE',
        font='Open Sans',
        pos=(0.03, 0), height=0.02, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-11.0);
text_Nap = visual.TextStim(win=win, name='text_Nap',
        text='N\nA\nP',
        font='Open Sans',
        pos=(-0.03, 0), height=0.02, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-12.0);
mouseresp = event.Mouse(win=win)
x, y = [None, None]
mouseresp.mouseClock = core.Clock()
text_resp = visual.TextStim(win=win, name='text_resp',
        text='Have you heard this excerpt before?',
        font='Open Sans',
        pos=(0, 4), height=0.05, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-14.0);
text_O4 = visual.TextStim(win=win, name='text_O4',
        text='4',
        font='Open Sans',
        pos=(0.110,0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-15.0);
text_O3 = visual.TextStim(win=win, name='text_O3',
        text='3',
        font='Open Sans',
        pos=(0.210, 0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-16.0);
text_O2 = visual.TextStim(win=win, name='text_O2',
        text='2',
        font='Open Sans',
        pos=(0.210, -0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-17.0);
text_O1 = visual.TextStim(win=win, name='text_O1',
        text='1',
        font='Open Sans',
        pos=(-0.110,-0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-18.0);
text_N1 = visual.TextStim(win=win, name='text_N1',
        text='1',
        font='Open Sans',
        pos=(-0.110,-0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-19.0);
text_N2 = visual.TextStim(win=win, name='text_N2',
        text='2',
        font='Open Sans',
        pos=(-0.210,-0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-20.0);
text_N3 = visual.TextStim(win=win, name='text_N3',
        text='3',
        font='Open Sans',
        pos=(-0.210,0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-21.0);
text_N4 = visual.TextStim(win=win, name='text_N4',
        text='4',
        font='Open Sans',
        pos=(-0.110,0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-22.0);
text_certain = visual.TextStim(win=win, name='text_certain',
        text='certain',
        font='Open Sans',
        pos=(0,0.325), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-23.0)
text_hasard = visual.TextStim(win=win, name='text_unsure',
        text='unsure',
        font='Open Sans',
        pos=(0,-0.325), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-24.0)
        
#define the "NO" button in the center of the grid
button_NO = visual.Rect(
        win=win,
        name='button_NO',
        width=0.1,  # Adjust the size as needed
        height=0.2,
        pos=(0, 0),  # Center of the grid
        fillColor=[0.8824, 0.9451, 1.0000],  # Light blue color
        lineColor=[-1.0, -1.0, -1.0],  # Black outline
        lineWidth=1.0,
        opacity=1.0
    )

# Add "NO" text on the button
text_NO = visual.TextStim(
        win=win,
        name='text_NO',
        text='NO',
        font='Open Sans',
        pos=(0, 0),  # Same position as the button
        height=0.03,  # Adjust font size as needed
        wrapWidth=None,
        ori=0.0,
        color=[-1.000, -1.000, -1.000],  # Black text
        colorSpace='rgb',
        opacity=1.0,
        languageStyle='LTR'
    )

# Draw the button and text
button_NO.draw()
text_NO.draw()

# Flip the screen to render everything
win.flip()
        
#-----------------------
# Stimulus Presentation
#-----------------------
if test_mode:
    n_stimulus_for_loop = test_n_stimulus
else :
    n_stimulus_for_loop = n_stimulus

break_count = 0
n_stimulus_each_break = math.ceil( n_stimulus_for_loop / (n_breaks+1) )

if not resume_flag:
    # new experiment: loop all
    stimulus_array_for_loop = range(n_stimulus_for_loop)
else:
    # resume mode: loop from break point
    # find the break point
    # find the last rating
    rating_cols = [item for item in sound_list2.columns if 'rating' in item]

    last_valid_row = -1
    for col in rating_cols:
        last_valid_index_col = sound_list2[col].last_valid_index()
        if last_valid_index_col is None:
            last_valid_index_col = -1
        last_valid_row = max(last_valid_row, last_valid_index_col)

    resume_sound_idx = last_valid_row + 1

    stimulus_array_for_loop = range(resume_sound_idx,n_stimulus_for_loop)

for sound_idx in stimulus_array_for_loop:
    cur_sound_name = sound_list2['sound'][sound_idx]
    cur_type = sound_list2['type'][sound_idx]
    cur_sound_path_1 = os.path.join(_thisDir, input_folder , cur_type, cur_sound_name) #individual stimuli
   
    mySound = sound.Sound(cur_sound_path_1, preBuffer=-1, volume=volume)
    # get sound duration
    duration = mySound.getDuration()
    sound_list2['duration'] [sound_idx] = duration
    write_value_to_excel(rating_xlsx_musicality2,'SoundList2',duration,cur_sound_name,'duration')

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

    sound_list2['post-rating'][sound_idx] = cur_pre_trial_rating
    write_value_to_excel(rating_xlsx_musicality2,'SoundList2',cur_pre_trial_rating,cur_sound_name,'post-rating')
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
        
    sound_list2['post-rating_confirm'][sound_idx] = cur_pre_trial_cfm_rating
    write_value_to_excel(rating_xlsx_musicality2,'SoundList2',cur_pre_trial_cfm_rating,cur_sound_name,'post-rating_confirm')
    # Define the mouse for interaction
    mouse = event.Mouse(win=win)

    # Prepare the grid with the components
    text_resp = visual.TextStim(win=win, name='text_resp',
        text='Have you heard this excerpt before?',
        font='Open Sans',
        pos=(0, 0.4), height=0.05, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR')

    # List of grid areas (buttons) with their text labels and positions
    grid_buttons = [
        {"name": "NO", "button": button_NO, "text": text_NO},
        {"name": "NAP_1", "button": nap_1, "text": text_N1},
        {"name": "NAP_2", "button": nap_2, "text": text_N2},
        {"name": "NAP_3", "button": nap_3, "text": text_N3},
        {"name": "NAP_4", "button": nap_4, "text": text_N4},
        {"name": "WAKE_1", "button": wake_1, "text": text_O1},
        {"name": "WAKE_2", "button": wake_2, "text": text_O2},
        {"name": "WAKE_3", "button": wake_3, "text": text_O3},
        {"name": "WAKE_4", "button": wake_4, "text": text_O4}
    ]

    # --- Main Routine ---
    selected_response = None
    while True:
        # Draw all components
        text_resp.draw()
        for grid_item in grid_buttons:
            grid_item["button"].draw()
            grid_item["text"].draw()

        # Flip the screen to render the components
        win.flip()

        # Check for mouse clicks
        if mouse.getPressed()[0]:  # Left button pressed
            mouse_x, mouse_y = mouse.getPos()  # Get mouse coordinates
            for grid_item in grid_buttons:
                button = grid_item["button"]
                # Check if the click is within the button's area
                if button.contains(mouse):
                    selected_response = grid_item["name"]  # Record the response
                    print(f"Selected response: {selected_response}")
                    break

        # Exit loop if a response is selected
        if selected_response is not None:
            break

        # Clear mouse press to avoid multiple selections
        mouse.clickReset()
    sound_list2['memory'][sound_idx] = selected_response
    write_value_to_excel(rating_xlsx_musicality2,'SoundList2',selected_response,cur_sound_name,'memory')
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
# End of Wake Musicality Rating 2
#------------------------

text = visual.TextStim(win=win, text="Congratulations! You have completed the experiment!"\
                       "\n\n Please wait for your experimenter to wrap up today's session. Wish you a pleasant evening! :)",\
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
# END
#------------------------