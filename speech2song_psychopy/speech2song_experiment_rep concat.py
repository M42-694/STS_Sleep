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

plugins.activatePlugins()
#win = visual.Window(fullscr=True, waitBlanking=False)
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

################################
# --- Parameter to control --- #
################################
# param exp

psychopyVersion = '2024.1.1'
expName = 'speech2song'
input_folder = 'input/stimuli/'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
# debug
resume_flag = False
test_mode = True
test_n_stimulus = 10
# sound presentation
volume = 1
record_after = 2           # trial - continuous slider: record time after the sound (sec)
interval_cross_sound = 1   # interval: sound presents after fixation (sec)
n_repeat = 16               # repetition time of stimulus
gap_time = 0.5             # the intetval between repetition (sec)
rep_interval_cross_sound = interval_cross_sound # interval: sound presents after click (sec) 
n_break = 2
# control mode
control_mode = 'key'   # 'key' for keyboard, 'mouse' for mouse
continue_key = 'return'  # 'return' for Enter, 'down' for ↓
# slider
slider_granularity=.1
slider_decimals=1
step_size = 0.5 # keyboard mode step size
slideSpeed = 50*slider_granularity

run_params = {"continuous_record_after": record_after,
            "interval_cross_sound": interval_cross_sound,
            "volume": volume,
            "n_repeat": n_repeat,
            "interval_dur_rep": gap_time,
            "rep_interval_cross_sound": rep_interval_cross_sound,
            "test_mode": test_mode,
            "test_n_stimulus": test_n_stimulus,
            "n_break": n_break,
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

##################################
# --- Prepare Sound Sequence --- #
##################################
def StimulusSeqInit(stimulus_list):
    ''' randomize stimulus sequence '''
    ''' modern Fisher–Yates shuffle '''
    n_stimulus = len(stimulus_list)
    ran_order = list(tuple(range(n_stimulus)))
    random.shuffle(ran_order)     
    ran_stimulus_list = stimulus_list.reindex(index = ran_order)
    ran_stimulus_list.reset_index(drop=True, inplace=True)
    return ran_stimulus_list

rating_xlsx_filename = op.join(output_path, 'rating.xlsx')

if not resume_flag:
    # create sound list
    file_list, sound_type = [], []
    for type in types:
        cur_file_list = os.listdir(os.path.join(input_folder, type))
        file_list = file_list + cur_file_list
        sound_type = sound_type + [type] * len(cur_file_list)

    sound_list = pd.DataFrame({'sound': file_list, 'type': sound_type})
    for shf in range(2):
        sound_list = StimulusSeqInit(sound_list)

    # add properties of sound
    sound_list['duration'] = None
    sound_list['pre-rating'] = None
    sound_list['pre-rating_confirm'] = None
    sound_list['post-rating'] = None
    sound_list['post-rating_confirm'] = None

    # save sound list to excel
    with pd.ExcelWriter(rating_xlsx_filename) as writer:
        sound_list.to_excel(writer, sheet_name='SoundList')
else:
    # read sound list
    sound_list = pd.read_excel(rating_xlsx_filename, sheet_name='SoundList')
    file_list = sound_list['sound']
    sound_type = sound_list['type']
    
n_stimulus = len(sound_list)


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
    color=[0, 0, 0])

# fixation cross
fixation = visual.shape.ShapeStim(win=win, 
								  vertices="cross", 
								  color='white', 
								  fillColor='white', 
								  contrast=contrast, 
								  size=max(win.size)/ratio_cross)

# Sdapt text to control mode
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
slider_ticks=[1,2,3,4,5]
slider_labels=['Strongly Speech-like','Speech-like','Neither Speech-like nor Song-like','Song-like','Strongly Song-like']
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
n_sound = n_stimulus
if not resume_flag:
    trial_instruct = "You will listen to " + str(n_sound) + " sound stimuli presented in " + str(n_break+1) + " blocks. "\
        "\n\n For each stimulus, it will be played once at first, and you need to \
        \n rate how much it sounds speech-like or song-like by a slider.\
        \n\n Then, the same stimulus will be repeated " + str(n_repeat) + " times. You can\
        \n change your rating during the repetition when you feel changes in perception.\
        \n\n Finally, the stimulus will be played once more, please rate it again. \
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
    n_stimulus_for_loop = n_stimulus

break_count = 0
n_stimulus_each_break = math.ceil( n_stimulus_for_loop / (n_break+1) )

if not resume_flag:
    # new experiment: loop all
    stimulus_array_for_loop = range(n_stimulus_for_loop)
else:
    # resume mode: loop from break point
    # find the break point
    # find the last rating
    rating_cols = [item for item in sound_list.columns if 'rating' in item]

    last_valid_row = -1
    for col in rating_cols:
        last_valid_index_col = sound_list[col].last_valid_index()
        if last_valid_index_col is None:
            last_valid_index_col = -1
        last_valid_row = max(last_valid_row, last_valid_index_col)

    resume_sound_idx = last_valid_row + 1

    stimulus_array_for_loop = range(resume_sound_idx,n_stimulus_for_loop)

for sound_idx in stimulus_array_for_loop:
    cur_sound_name = sound_list['sound'][sound_idx]
    cur_type = sound_list['type'][sound_idx]
    cur_sound_path = os.path.join(_thisDir, input_folder , cur_type, cur_sound_name)
    mySound = sound.Sound(cur_sound_path, preBuffer=-1, volume=volume)
    # get sound duration
    sound_list['duration'][sound_idx] = mySound.duration
    write_value_to_excel(rating_xlsx_filename,'SoundList',mySound.duration,cur_sound_name,'duration')

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
    play_sound(cur_sound_path, volume)
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

    sound_list['pre-rating'][sound_idx] = cur_pre_trial_rating
    write_value_to_excel(rating_xlsx_filename,'SoundList',cur_pre_trial_rating,cur_sound_name,'pre-rating')
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
        
    sound_list['pre-rating_confirm'][sound_idx] = cur_pre_trial_cfm_rating
    write_value_to_excel(rating_xlsx_filename,'SoundList',cur_pre_trial_cfm_rating,cur_sound_name,'pre-rating_confirm')


    #----------------------------
    # trial (stimulus repetition)
    #----------------------------
    if control_mode == 'key':
        above_text_str_continuous = "This excerpt will be repeated "+ str(n_repeat) + " times."\
        "\n\n If at any time you feel any changes, adjust the rating using ← and → keys."\
        "\n\n If you do not feel any changes, then you do not need to do anything."\
        "\n\n " + control_text + " to continue!"
    elif control_mode == 'mouse':
        above_text_str_continuous = "This excerpt will be repeated "+ str(n_repeat) + " times."\
        "\n\n If at any time you feel any changes, adjust the rating using mouse."\
        "\n\n If you do not feel any changes, then you do not need to do anything."\
        "\n\n " + control_text + " to continue!"
    text = visual.TextStim(win=win, text=above_text_str_continuous,\
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
    win.flip()  

    # set start position of mouse and marker
    initial_marker_pos = cur_pre_trial_cfm_rating if not cur_pre_trial_cfm_rating == error_slider_data_null else (slider_ticks[0] + slider_ticks[-1])/2
    oldRating = initial_marker_pos
    initial_rel_mouse_pos = [((initial_marker_pos-(slider_ticks[0] + slider_ticks[-1])/2) / (slider_ticks[-1] - slider_ticks[0])*2),0]
    initial_mouse_pos = [0,0]
    initial_mouse_pos[slider_orientation] = initial_rel_mouse_pos[slider_orientation] * slider_shape_width /2 * win.size[slider_orientation]

    slider.marker.color = marker_colour_continuous
    if control_mode == 'key':
        cur_trial_slider, cur_trial_slider_data  = slider_routine_continuous_key(win, slider, slider_shape, 
            slider_orientation, slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, slideSpeed, oldRating,
            cur_sound_path.replace('stimuli','rep_concatenated_'+str(n_repeat)+'times'), 1, record_after, rep_interval_cross_sound, gap_time, volume, step_size)
    elif control_mode == 'mouse':
        cur_trial_slider, cur_trial_slider_data  = slider_routine_continuous(win, slider, slider_shape, 
                slider_orientation, slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, slideSpeed, oldRating, mouse,
                cur_sound_path.replace('stimuli','rep_concatenated_'+str(n_repeat)+'times'), 1, record_after, rep_interval_cross_sound, gap_time, initial_mouse_pos, initial_marker_pos, volume)
        
    ratings = [item[0] for item in cur_trial_slider_data if item[1] >= rep_interval_cross_sound*1000]
    ratings = [cur_sound_name] + ratings
    times = [item[1] - rep_interval_cross_sound*1000 for item in cur_trial_slider_data if item[1] >= rep_interval_cross_sound*1000]
    times = [cur_sound_name] + times
    write_vector_to_excel_col(rating_xlsx_filename, 'slider', ratings)    
    write_vector_to_excel_col(rating_xlsx_filename, 'slider_time', times)    

    
    #-----------------------
    # post-trial
    #-----------------------
    text = visual.TextStim(win=win, text="This excerpt will be repeated one more time,"\
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
    # show fixation
    fixation.autoDraw = True
    win.mouseVisible = False
    win.flip()
    # an interval before presentation
    core.wait(interval_cross_sound)
    # play sound
    play_sound(cur_sound_path, volume)
    fixation.autoDraw = False 
    win.flip()
    # rate the sound
    if control_mode == 'mouse':
        win.mouseVisible = True
    #-----------------------
    # post-trial Rating
    #-----------------------
    oldRating = -1
    slider.marker.color = marker_colour_discrete
    above_text = visual.TextStim(win=win, text=above_text_str,\
        color="white",pos=(0, 0.3*win.size[1]/2), contrast=contrast, wrapWidth=max(win.size)/ratio_text_width, height= max(win.size)/ratio_text_size)
    if control_mode == 'key':
        _ , cur_post_trial_slider_data = slider_routine_discrete_key(win, slider, slider_shape, 
                slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
                   slider_decimals, slideSpeed, oldRating, above_text, step_size, end_key_name)
    elif control_mode == 'mouse':
        _ , cur_post_trial_slider_data = slider_routine_discrete(win, slider, slider_shape, slider_orientation, 
                                                                    slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, 
                                                                    slideSpeed, oldRating, mouse, above_text)
    
    # get post-trial rating and save    
    try:
        cur_post_trial_rating = cur_post_trial_slider_data[-1][0]
        oldRating = cur_post_trial_rating
    except IndexError:
        cur_post_trial_rating = error_slider_data_null
        oldRating = -1
      
    sound_list['post-rating'][sound_idx] = cur_post_trial_rating
    write_value_to_excel(rating_xlsx_filename,'SoundList',cur_post_trial_rating,cur_sound_name,'post-rating')
    core.wait(1)

    #-------------------------------
    # post-trial Rating CONFIRMATION
    #-------------------------------
    slider.marker.color = marker_colour_discrete
    above_text = visual.TextStim(win=win, text="Please confirm your rating."\
                                 "\n\n " + control_text + " to continue!",
        color="white",pos=(0, 0.3*win.size[1]/2), contrast=contrast, wrapWidth=max(win.size)/ratio_text_width, height= max(win.size)/ratio_text_size)
    if control_mode == 'key':
        _ , cur_post_trial_cfm_slider_data = slider_routine_discrete_key(win, slider, slider_shape, 
                slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
                   slider_decimals, slideSpeed, oldRating, above_text, step_size, end_key_name)
    elif control_mode == 'mouse':
        _ , cur_post_trial_cfm_slider_data = slider_routine_discrete(win, slider, slider_shape, slider_orientation, 
                                                                    slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, 
                                                                    slideSpeed, oldRating, mouse, above_text)
    
    # get post-trial rating and save    
    try:
        cur_post_trial_cfm_rating = cur_post_trial_cfm_slider_data[-1][0]
    except IndexError:
        cur_post_trial_cfm_rating = error_slider_data_null

    sound_list['post-rating_confirm'][sound_idx] = cur_post_trial_cfm_rating    
    write_value_to_excel(rating_xlsx_filename,'SoundList',cur_post_trial_cfm_rating,cur_sound_name,'post-rating_confirm')


    #------------------------------
    # Break Time
    #------------------------------
    if sound_idx == (break_count+1) * n_stimulus_each_break - 1 :
        text = visual.TextStim(win=win, text=" Well done! You finished the No." + str(break_count+1) +" block. It's break time now."\
            "\n If you'd like to have a break outside the room, please inform the experimenter."\
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
        break_count += 1

     
#-----------------------
# Ending
#-----------------------
text = visual.TextStim(win=win, text="Congratulations! You finished all excerpts!"\
                       "\n\n Please contact the experimenter."\
                       "\n\n Thanks for joining our experiment! Wish you a good day :)",\
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