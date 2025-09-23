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
prefs.hardware['audioLib'] = ['PTB']
prefs.hardware['audioDevice'] = 'Scarlett Solo USB'  
prefs.hardware['sampleRate'] = 44100 
prefs.hardware['audioLatencyMode'] = '0'
defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')


def core_wait_with_esc(wait_time):
    start_time = core.getTime()
    while core.getTime() - start_time < wait_time:
        keys = event.getKeys()
        if 'escape' in keys:
            core.quit()
        core.wait(0.01)

################################
# --- Parameter to control --- #
################################
resume_flag = False
psychopyVersion = '2024.1.1'
expName = 'speech2song'
input_rep_folder = 'input/rep_concatenated_8times'
output_folder = 'output/'
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
_thisDir = op.dirname(op.abspath(__file__))
os.chdir(_thisDir)

# create output folder for this subject and session and determine filename
filename = u'%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
output_path = _thisDir + os.sep + u'output/%s_%s_%s/%s' % (expInfo['participant'], expName, expInfo['date'],expInfo['session'])

os.makedirs(output_path, exist_ok=True)

volume = 1
n_repeat = 8
gap_time = 0.5
n_blocks = 3
stimulus_delay = 5
control_mode = 'key'
test_mode = True
fullscreen = False

play_xlsx_nap = op.join(output_path, 'nap_sns_list.xlsx')
sound_list_nap_b1 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_1')
sound_list_nap_b2 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_2')
sound_list_nap_b3 = pd.read_excel(play_xlsx_nap, sheet_name='Nap_Block_3')

file_list_b1 = sound_list_nap_b1['sound']
sound_type_b1 = sound_list_nap_b1['type']
file_list_b2 = sound_list_nap_b2['sound']
sound_type_b2 = sound_list_nap_b2['type']
file_list_b3 = sound_list_nap_b3['sound']
sound_type_b3 = sound_list_nap_b3['type']

print("Loaded sound_list_nap_b1, sound_list_nap_b2 and sound_list_nap_b3 from file.")

win_size = (1280, 720)
ratio_text_size = 40
ratio_text_width = 1
ratio_cross = 40
contrast = 1
full_screen = not test_mode

win = visual.Window(
    size=win_size,
    units="pix",
    fullscr=full_screen,
    color=[-1, -1, -1]
)

fixation = visual.shape.ShapeStim(win=win,
                                  vertices="cross",
                                  color='white',
                                  fillColor='white',
                                  contrast=contrast,
                                  size=max(win.size)/ratio_cross)

if control_mode == 'mouse':
    mouse = Mouse(visible=True, newPos=[0, 0])
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
    resume_position = 0
    snd = None

    while current_index < len(sound_indices):
        idx = sound_indices[current_index]
        cur_sound_name = sound_list_df['sound'][idx]
        cur_type = sound_list_df['type'][idx]
        cur_sound_path = os.path.join(_thisDir, input_folder, cur_type, cur_sound_name)

        print(f"Playing: {cur_sound_name}")
        try:
            snd = sound.Sound(cur_sound_path, preBuffer=-1, volume=volume)
            snd.play()
            start_time = core.getTime()

            while snd.status == 'playing':
                keys = event.getKeys()
                if 'space' in keys:
                    resume_position += core.getTime() - start_time
                    snd.stop()
                    paused = True
                    print(f"Paused at {resume_position:.2f}s. Press SPACE to resume.")
                    core.wait(0.3)
                    break
                if 'escape' in keys:
                    print("Exiting block early.")
                    snd.stop()
                    unplayed_stimuli.extend(list(sound_list_df['sound'])[current_index:])
                    log_df = pd.DataFrame({
                        'played': played_stimuli + [''] * (len(unplayed_stimuli)),
                        'unplayed': unplayed_stimuli + [''] * (len(played_stimuli) - len(unplayed_stimuli))
                    })
                    log_filename = os.path.join(output_log, f"{block_name}_play_log.csv")
                    log_df.to_csv(log_filename, index=False)
                    return
                core.wait(0.01)

            if paused:
                while True:
                    keys = event.getKeys()
                    if 'space' in keys:
                        print("Resuming...")
                        snd = sound.Sound(cur_sound_path, preBuffer=-1, volume=volume)
                        snd.seek(resume_position)
                        snd.play()
                        start_time = core.getTime()
                        resume_position = 0
                        paused = False
                        break
                    if 'escape' in keys:
                        print("Exiting block early during pause.")
                        unplayed_stimuli.extend(list(sound_list_df['sound'])[current_index:])
                        return
                    core.wait(0.01)

            played_stimuli.append(cur_sound_name)
            core.wait(stimulus_delay)
            current_index += 1

        except Exception as e:
            print(f"Error playing sound {cur_sound_name}: {e}")
            unplayed_stimuli.append(cur_sound_name)
            current_index += 1

    log_df = pd.DataFrame({
        'played': played_stimuli + [''] * (len(unplayed_stimuli)),
        'unplayed': unplayed_stimuli + [''] * (len(played_stimuli) - len(unplayed_stimuli))
    })
    log_filename = os.path.join(output_log, f"{block_name}_play_log.csv")
    log_df.to_csv(log_filename, index=False)
    print(f"Saved log for {block_name} to: {log_filename}")

# --- Playback Control Based on resume_flag ---
if resume_flag:
    resume_dlg = gui.Dlg(title="Resume Playback")
    resume_dlg.addText("Resume session")
    resume_dlg.addField("From which block? (1, 2, or 3):", choices=["1", "2", "3"])
    resume_input = resume_dlg.show()

    if resume_dlg.OK:
        resume_block = int(resume_input[0])
    else:
        print("Experimenter cancelled the resume dialog.")
        core.quit()

    if resume_block <= 1:
        play_sound_block(sound_list_nap_b1, input_rep_folder, output_path, 'Nap_Block_1')
        continue_dlg = gui.Dlg(title="Continue?")
        continue_dlg.addText("Continue to Block 2?")
        continue_dlg.addField("Yes/No:", choices=["Yes", "No"])
        if continue_dlg.show()[0] != "Yes":
            core.quit()
    else:
        print("Skipping Block 1")

    if resume_block <= 2:
        play_sound_block(sound_list_nap_b2, input_rep_folder, output_path, 'Nap_Block_2')
        continue_dlg = gui.Dlg(title="Continue?")
        continue_dlg.addText("Continue to Block 3?")
        continue_dlg.addField("Yes/No:", choices=["Yes", "No"])
        if continue_dlg.show()[0] != "Yes":
            core.quit()
    else:
        print("Skipping Block 2")

    if resume_block <= 3:
        play_sound_block(sound_list_nap_b3, input_rep_folder, output_path, 'Nap_Block_3')

    print("All blocks played.")

else:
    play_sound_block(sound_list_nap_b1, input_rep_folder, output_path, 'Nap_Block_1')
    continue_dlg = gui.Dlg(title="Continue?")
    continue_dlg.addText("Continue to Block 2?")
    continue_dlg.addField("Yes/No:", choices=["Yes", "No"])
    if continue_dlg.show()[0] != "Yes":
        core.quit()

    play_sound_block(sound_list_nap_b2, input_rep_folder, output_path, 'Nap_Block_2')
    continue_dlg = gui.Dlg(title="Continue?")
    continue_dlg.addText("Continue to Block 3?")
    continue_dlg.addField("Yes/No:", choices=["Yes", "No"])
    if continue_dlg.show()[0] != "Yes":
        core.quit()

    play_sound_block(sound_list_nap_b3, input_rep_folder, output_path, 'Nap_Block_3')
    print("All blocks played.")

#-----------------------
# End of Nap session 
#------------------------
print(f"All blocks played!")
