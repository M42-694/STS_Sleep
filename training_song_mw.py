####################
#### __ IMPORTS ____
####################
# General libraries
import os
import random
import pandas
import numpy as np
from datetime import datetime

# Psychopy. N.B. prefs must be set before importing psychopy modules
from psychopy import prefs
prefs.hardware['audioLib'] = ['sounddevice', 'PTB', 'pyo', 'pygame']
from psychopy import visual, sound, event, core, data, gui
from psychopy.hardware import keyboard
#defaultKeyboard = keyboard.Keyboard(backend='iohub')
defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, FINISHED)

from utils.slider_routine_discrete import slider_routine_discrete
from utils.slider_routine_discrete_key import slider_routine_discrete_key
from utils.utils import *

import serial

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
        SerialPortObj = serial.Serial("COM14", baudrate=115200, timeout=1)
        print("Serial port COM14 opened successfully.")
        #atexit.register(cleanup_serial)
    except serial.SerialException as e:
        print(f"[Serial Init Error] Could not open COM14: {e}")
        SerialPortObj = None
        
        
def send_trigger(code):
        try:
            SerialPortObj.write(reset_trigger_code)
            core.wait(0.005)
            SerialPortObj.write(code)
            core.wait(0.005)
        except Exception as e:
            print(f"[Trigger Error] Failed to send trigger {code}: {e}")

# Set Trigger initialisation 
trigger = True
port_name = 'COM14'
#trigger codes
reset_trigger_code = b'\x00' # 0
start_session = b'\x31' #1
stop_session = b'\x39'  #9

instruction_trigger = b'\x32'  # 2 - for all instruction slides
song_trigger = b'\x35'         # 5 for all song stimuli
speech_trigger = b'\x36'       # 6 for speech stimuli
response_trigger =  b'\x37' # 7 for response

if trigger:
    # select here the address of your port
    setup_serial()

def core_wait_with_esc(wait_time):
	# Custom loop to replace core.wait() and check for Esc press
	start_time = core.getTime()
	while core.getTime() - start_time < wait_time:
		keys = event.getKeys()  # Get any key presses
		if 'escape' in keys:    # If 'Esc' key is pressed
			core.quit()         # Quit PsychoPy
		core.w################################

# --- Parameter to control --- #
################################
# param exp
psychopyVersion = '2024.2.4'
expName = 'speech2song'
input_folder = './input/stimuli'
folder = './input/'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
# debug
resume_flag = False
test_mode = False
test_n_stimulus = 2

##############################
#### __ EXPERIMENT CONFIG ____
##############################
exp_name = 'speech2song_song'

# Store info about the participant and experiment session
expInfo = {'participant': f"{np.random.randint(0, 999999):06.0f}",
           'session': '001'}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=exp_name)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr() 
expInfo['expName'] = exp_name


# PARTICIPANT INFO
participant = expInfo['participant']
output_path = os.path.join('./output', participant + '_' + datetime.now().strftime("%d_%m_%Y_%H_%M"))
os.makedirs(output_path, exist_ok=True)
behavioural = pandas.DataFrame(columns=["File", "Block", 'Type_of_question', 
										"Key_given_answer", "Key_correct_answer", "Stim_trial", "Stim_behav",
										'Given_answer', 'Correct_answer', 'attention_probe','intention_probe'])

# PARAMETERS DEBUGGING
ask_behavioural = True
play_stimuli = True
full_screen = True 
p_behavioural = 1

# PARAMETERS EXP
# presentation
stim_IDs =  [3,6, 10, 11, 12, 13, 14, 15, 17, 18, 20] # short version # 11 stimuli
#stim_IDs = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20] # long version # 18 stiumuli
stim_types = ['song', 'speech']  #['melody', 'song', 'speech'] # 43 + 20 = 1h03 of experiment, 18 stimuli in each block
string_1st_slide = 'audio excerpts' #'songs, speech, and melodies'
nr_blocks = 2
df_time_lengths = pandas.read_csv(os.path.join(folder, 'stimuli_lengths.csv'))
df_lyrics_keywords = pandas.read_csv(os.path.join(folder, 'lyrics_keywords.csv'))
# audio
volume = 0.35
sampleRate = 44100 # Hz
startTime_behav = 20  # in sec
stopTime_behav = 28   # in sec
# visual
ratio_text_size = 40
ratio_text_width=2
ratio_cross = 40
contrast = 0.1


###############################
#### __ GENERATE EXP PARAM ____
###############################
# Genrate checkpoints
nr_stimuli = len(stim_IDs)
blocks_checkpoints = [nr_stimuli*x for x in range(nr_blocks)]

# GENERATE RANDOM STIMULI SEQUENCE FOR THIS SUBJECT AND SAVE IT
# For each stimulus, generate random sequence of [speech, song, melody]
# types_in_blocks: [nr_stimuli x 1] list where each item will be a 
# [1 x 3] list of strings, for instance ["melody", "speech", "song"]
types_in_blocks = []
for i in range(nr_stimuli):
	types_in_block = random.sample(stim_types, nr_blocks)
	# assert that there are no repeted versions of the stimulus (e.g. two melodies)
	assert len(types_in_block) == len(set(types_in_block))
	types_in_blocks.append(types_in_block)

# Generate final stimulus sequence. For each block generate a ordered sequence of IDs.
# Then, for each ID, check the appropriate stimulus type (speech, song or melody) which
# was decided in the previous loop. Shuffle the list and save the final stimulus sequence.
# Save useful metadata: block in which will be played and position in the block sequence.
stim_seq = []
block_seq = []
count_in_block_seq = []
# for each block generate a random list of IDs
for i in range(nr_blocks):
	file_seq_in_block = []
	# create a list of audio file names
	for j, id in enumerate(stim_IDs):
		typ = types_in_blocks[j][i]
		name_file = os.path.join(typ, f"{id:02d}_{typ}.wav")  # ensures 01, 02, ...
		file_seq_in_block.append(name_file)
		block_seq.append(i+1)
		count_in_block_seq.append(j+1)

	# randomize the list of file names
	random.shuffle(file_seq_in_block)
	stim_seq = stim_seq + file_seq_in_block
# assert contains unique stimuli file names and no stimulus is repeated twice
assert len(stim_seq) == len(set(stim_seq))

# Save other useful metadata such as stimulus ID, type, time length 
IDs_seq = []
types_seq = []
time_lengths_seq = []
for j, filename in enumerate(stim_seq):
    base = os.path.basename(filename)  # '01_song.wav'
    types_seq.append(base.split('_')[1].split('.')[0])  # 'song' or 'speech'
    IDs_seq.append(base.split('_')[0])                 # '01', '02', etc.
    time_lengths_seq.append(
        df_time_lengths.loc[df_time_lengths['File'] == base, 'Length'].values[0]
    )

# Save stimulus sequence and metadata immediatelty
df = pandas.DataFrame(data={"File": stim_seq, "ID": IDs_seq, "Type": types_seq, "Block": block_seq, "Count in block": count_in_block_seq, "Length": time_lengths_seq})
df.to_csv(os.path.join(output_path, 'stimuli_sequence.csv'), sep=',',index=False)

############################
#### __ PSYCHOPY CONFIG ____
############################ 
win = visual.Window(
	size=[800, 600],
	units="pix",
	fullscr=full_screen,
	color=[-1, -1, -1]
)
# Calculate dynamic parameters from `win`
win_width, win_height = win.size
win.mouseVisible = False

fixation = visual.shape.ShapeStim(win=win, 
								  vertices="cross", 
								  color='white', 
								  fillColor='white', 
								  contrast=contrast, 
								  size=max(win.size)/ratio_cross)
                                  
##################################
#### __SLIDER ROUTINE PARAMETER INITIALIZATION ____
###############################

# slider
continue_key = 'space'
slider_granularity=.1
slider_decimals=1
step_size = 0.5 # keyboard mode step size
slideSpeed = 30*slider_granularity # not needed

# Key-based discrete rating (used across all non-slider responses)
key_to_rating = {'d': 1, 'f': 2, 'g': 3, 'h': 4, 'j': 5}
rating_keys = list(key_to_rating.keys())
rating_values = list(key_to_rating.values())

# For numeric answers (attention, content questions)
numeric_keys_1to5 = ["1", "2", "3", "4", "5"]
numeric_keys_1to4 = ["1", "2", "3", "4"]

startClock = core.Clock()
slider_width=.47
slider_height=.1
slider_orientation=0
slider_ticks=[1,2,3,4]
slider_labels=['completely intentional','somewhat intentional','somewhat involuntary','competely involuntary']
sliding = 0
oldRating=-1
marker_colour_discrete='blue'
marker_size=.1
sliderColour='LightGray'
error_slider_data_null = -99

# Initialize components for Routine "trial"
trialClock = core.Clock()
slider_shape_width = 0.5
slider_shape_height = 0.5
margin_ratio_horizontal = 1.1
slider_shape = visual.Rect(win=win, name='slider_shape',
    width= win_width*slider_shape_width*margin_ratio_horizontal, height=win_height*slider_shape_height, 
    ori=0, pos=(0, 0), lineWidth=1, lineColor=[0,0,0], lineColorSpace='rgb',
    fillColor=[0,0,0], fillColorSpace='rgb', opacity=1, depth=-2.0, interpolate=True, )

slider = visual.Slider(win=win, name='slider',
    size=(win_width*slider_width, slider_height*win_height/2), pos=(0, -win_height * 0.1), 
    labels=slider_labels, ticks=slider_ticks, granularity=slider_granularity, 
    style=['rating'], color=sliderColour, flip=False, depth=-3)
    
Idx = 0
for label in slider.labelObjs:
    label.height = win_height * 0.01  # Smaller font size for labels
    label.wrapWidth = win_width * 0.02  # Prevent labels from overflowing
    label.text=slider_labels[Idx]
    Idx+=1
slider.marker.color=marker_colour_discrete

############################
#### __ EXPERIMENT ____
############################ 
# INTRODUCTION
# Slide 1
#Trigger to begin new instruction
if trigger:
    SerialPortObj.write(reset_trigger_code)
    #SerialPortObj.flush()
    core.wait(0.005)

    SerialPortObj.write(start_session)
    #SerialPortObj.flush()
    core.wait(0.005)
    
text = visual.TextStim(win=win, text="Welcome! \
	\n\nDuring this experiment, you will listen to " + string_1st_slide + ".\
	\nThe recorded data will be used to study how our brains process speech and song.\
	\n\nPress a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False

# Slide 2
text = visual.TextStim(win=win, text="We would like you to pay attention to the audio stimuli as much as possible.\
	\n\nThis means trying to follow the melodies, and understand what's said in the lyrics.\
	\n After each excerpt, we will ask you some questions to assess your attention. Please try to answer the best you can.\
	\n\nPress a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False

# Slide 3
text = visual.TextStim(win=win, text="The experiment consists of " + str(nr_blocks) + " blocks, "\
	"each one counting " + str(nr_stimuli) + " stimuli.\
	\n\nBetween blocks, there is a pause when you can stretch and drink water if you wish.\
	 You can also move between trials before pressing the key to starts the new stimuli.\
	\n Remember, you can always call the experimenter if you wish to stop \
	\n\n Press a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False

# Slide 4
text = visual.TextStim(win=win, text="While the stimuli are played, you should minimize movements and eye blinking as they highly impact the quality of the recordings.\
	\n\n You will be asked to close your eyes during the audio presentation phase.\
	\n\n Press a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False

# Slide 5
text = visual.TextStim(win=win, text=" Once each audio excerpt is done (i.e when you hear silence), you can open your eyes to answer the questions that follow.\
	\n\n Press a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False

# Slide 6
if trigger:
	#Trigger to begin new instruction
	SerialPortObj.write(reset_trigger_code)
	#SerialPortObj.flush()
	core.wait(0.005)

	SerialPortObj.write(instruction_trigger)
	#SerialPortObj.flush()
	core.wait(0.005)
text = visual.TextStim(win=win, text="We are almost ready! Enjoy listening!\.\
	\n\nWhen you're ready, press a key to start the experiment!", 
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False

# Stimuli presentation begins
for i, stim in enumerate(stim_seq):

	# Slide intro to block if new block starts
	if i in blocks_checkpoints:	
		text = visual.TextStim(win=win, text="Block nr " + str(block_seq[i]) + " is about to start."\
			"\n\n If you need to move or to need a short break, use this time!"
			"\n\n When you're ready, press a key", 
			color="white",
			contrast=contrast,
			wrapWidth=max(win.size)/ratio_text_width,
			height= max(win.size)/ratio_text_size)
		text.autoDraw = True
		win.flip()
		event.waitKeys()
		text.autoDraw = False

	# Slide intro of each stimulus
	if trigger:
		#Trigger to begin new instruction
		SerialPortObj.write(reset_trigger_code)
		#SerialPortObj.flush()
		core.wait(0.005)

		SerialPortObj.write(instruction_trigger)
		 #SerialPortObj.flush()
		core.wait(0.005)
	text = visual.TextStim(win=win, text="Block " + str(block_seq[i]) +\
							"\nTrial " + str(count_in_block_seq[i]) + "/" + str(nr_stimuli) +\
							# "\n\nID: " + str(IDs_seq[i]) +\
							# "\nType: " + str(types_seq[i]) +\
							# "\nLength in seconds: " + str(time_lengths_seq[i]) +\
							"\n\n Press a key to listen!",  
							color="white",
							contrast=contrast,
							wrapWidth=max(win.size)/ratio_text_width,
							height= max(win.size)/ratio_text_size)
	text.autoDraw = True
	win.flip()
	event.waitKeys()
	text.autoDraw = False	

	# Draw fixaxtion cross
	#fixation.autoDraw = True
	text = visual.TextStim(win=win, text="Remember to keep your eyes closed when the audio is playing!",  
							color="white",
							contrast=contrast,
							wrapWidth=max(win.size)/ratio_text_width,
							height= max(win.size)/ratio_text_size)
	text.autoDraw = True
	win.flip()

	
	# Play sound and disable keyboard for the time the stimulus is played
	# Get stimulus info
	stim_file = stim_seq[i]              # e.g. '01_song.wav'
	typ = types_seq[i].lower()           # e.g. 'song' or 'speech'
	stim_path = os.path.join(input_folder, stim_file)

	# Load and play sound
	if play_stimuli:
		mySound = sound.Sound(stim_path, preBuffer=-1, volume=volume)
		# Send appropriate trigger based on type
		if trigger:
		 	if typ == 'song':
		 		 send_trigger(song_trigger)
		 	elif typ == 'speech':
		 		send_trigger(speech_trigger)
		 	else:
		 		print(f"Unknown stimulus type: {typ}, no trigger sent.")
		mySound.play()
		# Block until audio finishes playing
		core.wait(mySound.getDuration() + 0.1)
	#fixation.autoDraw = False 
	text.autoDraw = False

	if ask_behavioural:
		# Ask behavioural questions 100% of the time [previously set to 20% when mental state probes were not present]
		if np.random.choice([1, 0], p=[p_behavioural, 1-p_behavioural]):
			text = visual.TextStim(win=win, text="Attention! Please answer the following questions to the best you can! \
												  Press a key when you're ready!", 
									color="white",
									contrast=contrast,
									wrapWidth=max(win.size)/ratio_text_width,
									height= max(win.size)/ratio_text_size)
			text.autoDraw = True
			win.flip()
			event.waitKeys()
			text.autoDraw = False
			# Ask first question on level of attention / mental state
			if trigger:
				send_trigger(instruction_trigger)
			text = visual.TextStim(
					win=win,
					text=("What was your attention focused on when listening?"\
					 	"\n\n Use the keys 1 to 5 to responsd \n\n " \
					 	  " [1] On the excerpt\n" \
					 	 " [2] On something else, but influenced by the excerpt\n" \
					 	  " [3] On something totally unrelated to the excerpt\n" \
					 	  " [4] On nothing\n" \
					 	 " [5] I don't know anymore"),
					color="white",
					contrast=contrast,
					wrapWidth=max(win.size)/ratio_text_width,
					height= max(win.size)/ratio_text_size,
			)
			text.autoDraw = True
			win.flip()
			# Wait for a valid response for the second question
			# Wait for valid key response
			rating_value = None
			while rating_value is None:
				if trigger:
					 send_trigger(response_trigger)
				response_key = event.waitKeys(keyList=rating_keys)[0]  # rating_keys = ['d', 'f', 'g', 'h', 'j']
				if response_key in key_to_rating:
					rating_value = key_to_rating[response_key]  # Maps to [1–5]

			text.autoDraw = False
			# Ask Second question on level of attention and mental state 
			slider.marker.color = marker_colour_discrete
			if trigger:
				send_trigger(instruction_trigger)
			text = "Was your state of mind (attentive or distractive) intentional?\n"\
				 "Please use keys 1 to 5 for rating." \
				 "\n" + "Press " + continue_key + " key to continue!"
			above_text = visual.TextStim(win=win, text=text,\
				 color="white", contrast=contrast,wrapWidth=max(win.size)/ratio_text_width,height= max(win.size)/ratio_text_size,pos=(0, 0.3*win.size[1]/2))
			#give keyboard response using slider scale
			oldRating = None

			state_trial_slider_data, rating_info = slider_routine_discrete_key(win, slider, slider_shape, 
				 slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
				 slider_decimals, oldRating, above_text,continue_key)
			if trigger:
				send_trigger(response_trigger)

			# get the response and save
			try:
				state_trial_rating= rating_info[0][0]
				state_trial_rt= rating_info[0][1]
			except IndexError:
				state_trial_rating = error_slider_data_null
				state_trial_rt = None

			above_text.autoDraw = False
			slider.autoDraw = False
			win.flip()

			if typ == 'speech':	
				type_of_question = 'content'
			elif typ == 'song':
				type_of_question = random.choice(['content'])

			if type_of_question == 'content':
				# Extract first the keywords assosciated with this stimulus, i.e. the right keywords and then other two possible answers
				correct_answer= df_lyrics_keywords.loc[df_lyrics_keywords['ID'] == int(IDs_seq[i])]['Keywords'].values[0]
				possible_answers = list(np.random.choice([x for x in df_lyrics_keywords['Keywords'].values if x not in [correct_answer]], 2))

				# Create the answers vector and shuffle it
				possible_answers.append(correct_answer)
				random.shuffle(possible_answers)

				# Extract the index of correct answer to compare it to the the answer of the user
				key_correct_answer = str(possible_answers.index(correct_answer) + 1)
				if trigger:
					send_trigger(instruction_trigger)
				# Ask the question
				text = visual.TextStim(win=win, text="Which group of words best describes the lyrics you just heard?\
									    \n\n Type the number of the correct answer using the keyboard" +
									    "\n\n [1] " + possible_answers[0] + 
										"\n [2] " + possible_answers[1] + 
										"\n [3] " + possible_answers[2] + 
										"\n [4]None of the above", 
									color="white",
									contrast=contrast,
									 wrapWidth=max(win.size)/ratio_text_width,
									height= max(win.size)/ratio_text_size)
				text.autoDraw = True
				win.flip()
				# Get the response for the first question
				while True:
					response_key = event.waitKeys(keyList=rating_keys)[0]
					if trigger:
						send_trigger(response_trigger)
					if response_key in key_to_rating:
						numeric_response = key_to_rating[response_key]
						key_given_answer = str(numeric_response)
						if numeric_response == 4:
							given_answer = "None of the above"
						else:
							given_answer = possible_answers[numeric_response - 1]
						break 
				text.autoDraw = False 
				# behavioural = behavioural.append({"File":stim_seq[i], 
				# 							"Block":block_seq[i], 
				# 							"Type_of_question":type_of_question, 
				# 							"Key_given_answer":key_given_answer,
				# 							"Key_correct_answer":key_correct_answer,
				# 							"Given_answer":given_answer,
				# 							"Correct_answer":correct_answer,
				# 							"Correctness":(key_given_answer == key_correct_answer)}, ignore_index=True)
				# 							"Key_probe_answer":key_probe_answer,
				# 							"state_slider_answer":state_trial_slider_data,
				behavioural.loc[i, 'File'] = stim_seq[i]
				behavioural.loc[i, 'Block'] = block_seq[i]
				behavioural.loc[i, 'Type_of_question'] = type_of_question
				behavioural.loc[i, 'Key_given_answer'] = key_given_answer
				behavioural.loc[i, 'Key_correct_answer'] = key_correct_answer
				behavioural.loc[i, 'Given_answer'] = given_answer
				behavioural.loc[i, 'Correct_answer'] = correct_answer
				behavioural.loc[i, 'Correctness'] = (key_given_answer == key_correct_answer)
				behavioural.loc[i, 'attention_probe'] = rating_value
				behavioural.loc[i, 'intention_probe'] = state_trial_rating

			# Save behavioural responses
			behavioural.to_csv(os.path.join(output_path, 'answers_to_questions.csv'), sep=',',index=False)

### END EXPERIMENT
text = visual.TextStim(win=win, text="Congragulations! You have completed the first phase of today's experiment!\
					   \n\n You can wait for the experimenter to return, and instruct you on the next phase.\
					   \n\n Press one final time a key to end the experiment!", 
					   color="white",
					   contrast=contrast,
					   wrapWidth=max(win.size)/ratio_text_width,
					   height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False
if trigger:
    send_trigger(stop_session)

win.close()
