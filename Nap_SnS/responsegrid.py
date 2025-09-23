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
# param exp
psychopyVersion = '2024.1.1'
expName = 'speech2song'
input_folder = 'input/stimuli/'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
# debug  
resume_flag = False
test_mode = True
test_n_stimulus = 2
# sound presentation
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
# control mode
control_mode = 'key'   # 'key' for keyboard, 'mouse' for mouse
continue_key = 'return'  # 'return' for Enter, 'down' for ↓
# Adapt text to control mode
if control_mode == 'key':
    end_key_name = continue_key
    control_text = 'Press ' + end_key_name
elif control_mode == 'mouse':
    control_text = 'Click'
    mouse = Mouse(visible=True, newPos=[0,0])
    mouse = event.Mouse(win=win)

   
# --- Initialize components for Routine "memory_old_new" ---

wake_1 = visual.ShapeStim(
        win=win, name='wake_1',
        size=(0.4, 0.2), vertices='triangle',
        ori=225.0, pos=(0.0975, -0.2175), anchor='None',
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
cross = visual.ShapeStim(
        win=win, name='cross', vertices='cross',
        size=(0.120, 0.575),
        ori=0.0, pos=(0, 0), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[-1.0000, -1.0000, -1.0000], fillColor=[0.8824, 1.0000, 1.0000],
        opacity=None, depth=-9.0, interpolate=True)
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
        pos=(0, 0.4), height=0.05, wrapWidth=None, ori=0.0, 
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
text_O3 = visual.TextStim(win=win, name='text_W3',
        text='3',
        font='Open Sans',
        pos=(0.210, 0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-16.0);
text_O2 = visual.TextStim(win=win, name='text_W2',
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
        depth=-23.0);
text_unsure = visual.TextStim(win=win, name='text_unsure',
        text='unsure',
        font='Open Sans',
        pos=(0,-0.325), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-24.0);
        
# Define the "NO" button in the center of the grid
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
        
# Define the mouse for interaction
mouse = event.Mouse(win=win)

# Prepare the grid with the components
text_resp = visual.TextStim(win=win, name='text_resp',
        text='Have you heard this excerpt before?',
        pos=(0, 2.4), height=0.05, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None)

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