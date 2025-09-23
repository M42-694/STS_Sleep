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

   



# Dynamically adjust grid layout based on window size
grid_width, grid_height = 0.5, 0.5  # Overall grid size as a proportion of the window
triangle_size = (grid_width * 0.5, grid_height * 0.25)  # Size of each triangle
button_size = (grid_width * 0.2, grid_height * 0.2)  # Size of the central "NO" button

# Define the positions of the triangles
positions = {
    "NAP_4": (-grid_width * 2.5, grid_height * 0.5),
    "NAP_3": (-grid_width * 2.75, grid_height * 0.25),
    "NAP_2": (-grid_width * 2.75, -grid_height * 0.25),
    "NAP_1": (-grid_width * 2.5, -grid_height * 0.5),
    "WAKE_1": (grid_width * 2.5, -grid_height * 0.5),
    "WAKE_2": (grid_width * 2.75, -grid_height * 0.25),
    "WAKE_3": (grid_width * 2.75, grid_height * 0.25),
    "WAKE_4": (grid_width * 2.5, grid_height * 0.5),
}

# Define orientation angles for each triangle
orientations = {
    "NAP_4": 45, "NAP_3": 225, "NAP_2": 315, "NAP_1": 135,
    "WAKE_1": 135, "WAKE_2": 315, "WAKE_3": 225, "WAKE_4": 45
}

# Define colors for the triangles (left = blue, right = green)
colors = {
    "NAP_4": "blue", "NAP_3": "blue", "NAP_2": "blue", "NAP_1": "blue",
    "WAKE_1": "green", "WAKE_2": "green", "WAKE_3": "green", "WAKE_4": "green"
}

# Define labels for each triangle
labels = {
    "NAP_4": "4", "NAP_3": "3", "NAP_2": "2", "NAP_1": "1",
    "WAKE_1": "1", "WAKE_2": "2", "WAKE_3": "3", "WAKE_4": "4"
}

# Create the grid components
grid_buttons = []
for name, pos in positions.items():
    button = visual.ShapeStim(
        win=win,
        name=name,
        size=triangle_size,
        vertices="triangle",
        ori=orientations[name],
        pos=pos,
        fillColor=colors[name],
        lineColor="white",
        lineWidth=1.0
    )
    label = visual.TextStim(
        win=win,
        text=labels[name],
        pos=pos,
        height=grid_height * 0.1,
        color="white",
        wrapWidth=None
    )
    grid_buttons.append({"name": name, "button": button, "text": label})

# Create the central "NO" button
button_NO = visual.Rect(
    win=win,
    name="button_NO",
    width=button_size[0],
    height=button_size[1],
    pos=(0, 0),
    fillColor="white",
    lineColor="black",
    lineWidth=1.0
)
text_NO = visual.TextStim(
    win=win,
    text="NO",
    pos=(0, 0),
    height=grid_height * 0.1,
    color="black"
)

# Add certainty and unsure labels
text_certain = visual.TextStim(
    win=win,
    text="certain",
    pos=(0, grid_height * 0.6),
    height=grid_height * 0.08,
    color="white"
)
text_unsure = visual.TextStim(
    win=win,
    text="unsure",
    pos=(0, -grid_height * 0.6),
    height=grid_height * 0.08,
    color="white"
)

# --- Main Routine ---
selected_response = None
mouse = event.Mouse(win=win)
while True:
    # Draw the grid components
    for grid_item in grid_buttons:
        grid_item["button"].draw()
        grid_item["text"].draw()
    button_NO.draw()
    text_NO.draw()
    text_certain.draw()
    text_unsure.draw()

    # Flip the screen to render the components
    win.flip()

    # Check for mouse clicks
    if mouse.getPressed()[0]:  # Left button pressed
        for grid_item in grid_buttons:
            if grid_item["button"].contains(mouse):
                selected_response = grid_item["name"]
                print(f"Selected response: {selected_response}")
                break
        if button_NO.contains(mouse):
            selected_response = "NO"
            print("Selected response: NO")
            break

    # Exit loop if a response is selected
    if selected_response is not None:
        break

    # Clear mouse press to avoid multiple selections
    mouse.clickReset()

# Print the selected response
print(f"Final response: {selected_response}")
