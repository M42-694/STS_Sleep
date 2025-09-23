from psychopy import visual, core, event
# --- Import packages ---
from numpy.random import random
import pandas as pd
import numpy as np
import os 
import random
import math
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
from psychopy.event import Mouse
from psychopy.hardware import keyboard
from datetime import datetime
# Setup window
win = visual.Window(fullscr=True, color='black')
mouse = event.Mouse(win=win)
mouse.mouseClock = core.Clock()

# Constants
scale = 0.7
square_half = 0.35 * scale  # half-width of full grid area
tri_size = (0.25 * scale, 0.25 * scale)
text_height = 0.035 * scale

# Instruction text
text_question = visual.TextStim(win, text="Have you heard this word before?", pos=(0, 0.45), height=text_height, color='white')
mouseresp = event.Mouse(win=win)
x, y = [None, None]
mouseresp.mouseClock = core.Clock()
    # --- Initialize components for Routine "memory_old_new" ---
memorytest = sound.Sound('A', secs=-1, stereo=True, hamming=True,
name='memorytest')
memorytest.setVolume(0.8)
gotValidClick = False  # until a click is received
mouseresp.clicked_name = []
Nap_1 = visual.ShapeStim(
        win=win, name='Nap_1',
        size=(0.4, 0.2), vertices='triangle',
        ori=225.0, pos=(0.0975, -0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000,1.0000,1.0000],
        opacity=None, depth=-1.0, interpolate=True)
Nap_2 = visual.ShapeStim(
        win=win, name='Nap_2',
        size=(0.4, 0.2), vertices='triangle',
        ori=45.0, pos=(0.25, -0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000,1.0000,1.0000],
        opacity=None, depth=-2.0, interpolate=True)
Nap_3 = visual.ShapeStim(
        win=win, name='Nap_3',
        size=(0.4, 0.2), vertices='triangle',
        ori=135.0, pos=(0.25, 0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-3.0, interpolate=True)
Nap_4 = visual.ShapeStim(
        win=win, name='Nap_4',
        size=(0.4, 0.2), vertices='triangle',
        ori=315.0, pos=(0.0975, 0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-4.0, interpolate=True)
Wake_4 = visual.ShapeStim(
        win=win, name='Wake_4',
        size=(0.4, 0.2), vertices='triangle',
        ori=45.0, pos=(-0.0975, 0.2175), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-5.0, interpolate=True)
Wake_3 = visual.ShapeStim(
        win=win, name='Wake_3',
        size=(0.4, 0.2), vertices='triangle',
        ori=225.0, pos=(-0.25, 0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-6.0, interpolate=True)
Wake_2 = visual.ShapeStim(
        win=win, name='Wake_2',
        size=(0.4, 0.2), vertices='triangle',
        ori=315.0, pos=(-0.25, -0.075), anchor='center',
        lineWidth=1.0,     colorSpace='rgb',  lineColor=[0.8824, 0.9451, 1.0000], fillColor=[1.0000, 1.0000, 1.0000],
        opacity=None, depth=-7.0, interpolate=True)
Wake_1 = visual.ShapeStim(
        win=win, name='Wake_1',
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
text_Nap = visual.TextStim(win=win, name='text_Nap',
        text='N\nA\nP',
        font='Open Sans',
        pos=(0.03, 0), height=0.02, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-11.0);
text_Wake = visual.TextStim(win=win, name='text_Wake',
        text='W\nA\nK\nE',
        font='Open Sans',
        pos=(-0.03, 0), height=0.02, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-12.0);
mouseresp = event.Mouse(win=win)
x, y = [None, None]
mouseresp.mouseClock = core.Clock()
text_resp = visual.TextStim(win=win, name='text_resp',
        text='Have you heard this speech phrase on loop before?',
        font='Open Sans',
        pos=(0, 0.4), height=0.05, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-14.0);
text_N4 = visual.TextStim(win=win, name='text_N4',
        text='4',
        font='Open Sans',
        pos=(0.110,0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-15.0);
text_N3 = visual.TextStim(win=win, name='text_N3',
        text='3',
        font='Open Sans',
        pos=(0.210, 0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-16.0);
text_N2 = visual.TextStim(win=win, name='text_N2',
        text='2',
        font='Open Sans',
        pos=(0.210, -0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-17.0);
text_N1 = visual.TextStim(win=win, name='text_N1',
        text='1',
        font='Open Sans',
        pos=(-0.110,-0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-18.0);
text_W1 = visual.TextStim(win=win, name='text_W1',
        text='1',
        font='Open Sans',
        pos=(-0.110,-0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-19.0);
text_W2 = visual.TextStim(win=win, name='text_W2',
        text='2',
        font='Open Sans',
        pos=(-0.210,-0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-20.0);
text_W3 = visual.TextStim(win=win, name='text_W3',
        text='3',
        font='Open Sans',
        pos=(-0.210,0.085), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-21.0);
text_W4 = visual.TextStim(win=win, name='text_W4',
        text='4',
        font='Open Sans',
        pos=(-0.110,0.175), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-22.0);
text_certain = visual.TextStim(win=win, name='text_certain',
        text='Certain',
        font='Open Sans',
        pos=(0,0.325), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-23.0);
text_uncertain = visual.TextStim(win=win, name='text_hasard',
        text='Uncertain',
        font='Open Sans',
        pos=(0,-0.325), height=0.03, wrapWidth=None, ori=0.0, 
        color=[-1.000,-1.000,-1.000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-24.0);
memory_old_newComponents = [
    Wake_1, Wake_2, Wake_3, Wake_4,
    Nap_1, Nap_2, Nap_3, Nap_4,
    text_Wake, text_Nap,
    text_certain, text_uncertain,
    text_resp, mouseresp
]
clickableList = [Wake_1, Wake_2, Wake_3, Wake_4,
    Nap_1, Nap_2, Nap_3, Nap_4,
    ]

if gotValidClick:
    continueRoutine = False
# --- Extract mouse response info ---
resp_label = mouseresp.clicked_name[-1]  # e.g., 'NAP_3'
resp_x = mouseresp.x[-1]
resp_y = mouseresp.y[-1]
resp_time = mouseresp.time[-1]

