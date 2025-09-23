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

################################
# --- Parameter to control --- #
################################
# param exp
psychopyVersion = '2024.2.4'
expName = 'speech2song'
input_folder = 'input/stimuli/'
input_rep_folder = 'input/rep_concatenated_8times'
output_folder = 'output/'
types = ["song", "speech"]     # illusion - song, control - speech
resume_flag = False
##########################################
### ___ EXPERIMENT-PARTICIPANT SETUP __###
##########################################
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
    # Split and assign group names in one step
    speech_groups = [
        speech_stimuli.iloc[i::len(group_names)].copy().assign(stim_group=group_name)
        for i, group_name in enumerate(group_names)
    ]

    song_groups = [
        song_stimuli.iloc[i::len(group_names)].copy().assign(stim_group=group_name)
        for i, group_name in enumerate(group_names)
    ]

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
    sound_list_wake_b1['pre-rating'] = None
    sound_list_wake_b1['rep-rating'] = None
    sound_list_wake_b1['time'] = None
    sound_list_wake_b1['rep-rating-confirm'] = None
    sound_list_wake_b2['pre-rating'] = None
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