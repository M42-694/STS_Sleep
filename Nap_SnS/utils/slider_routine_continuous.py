# --- Import packages ---
from psychopy import prefs
from psychopy import plugins
from psychopy import core
from psychopy.constants import (NOT_STARTED, FINISHED)
from psychopy.hardware import keyboard
from psychopy import sound

import threading
import time

plugins.activatePlugins()
prefs.hardware['audioLib'] = ['sounddevice', 'PTB', 'pyo', 'pygame'] #'ptb'
prefs.hardware['audioLatencyMode'] = '0'

defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')

class Clock:
    def __init__(self):
        self.start_time = time.time()
    def getTime(self):
        return time.time() - self.start_time

def play_sound_rep(file, volume, n_repeat, gap, wait_time):
    time.sleep(wait_time)
    for r in range(n_repeat):
        mySound = sound.Sound(file, volume=volume)	
        repClock = Clock()
        cur_sound_start = repClock.getTime()
        mySound.play()
        while True:
            if repClock.getTime() > cur_sound_start + mySound.getDuration() + gap:
                break
            time.sleep(0.1)

def slider_routine_continuous(win, slider, slider_shape, 
            slider_orientation, slider_ticks, slider_granularity, slider_shape_width, slider_decimals, sliding, slideSpeed, oldRating, mouse,
            mySound_file, n_repeat, record_after, rep_interval_cross_sound, gap_time, initial_mouse_pos, initial_marker_pos, volume):
    frameTolerance = 0.001  # how close to onset before 'same' frame
    trialClock = core.Clock()
    continueRoutine = True
    # update component parameters for each repeat
    if slider_granularity == 0:
        slider_granularity = .1
    sliding = 0
    oldRating = -1
    slider_data=[]
    last_rating = -1
    # what are the assumed key statuses at the start of the routine
    status =['up', 'up', 'up']

    # Set the initial mouse position
    mouse.setPos(initial_mouse_pos)
    # Set the initial marker position
    slider.markerPos = initial_marker_pos
    mouseRec=mouse.getPos()
    slider.reset()
    # keep track of which components have finished
    trialComponents = [slider_shape, slider]
    for thisComponent in trialComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    frameN = -1
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    trialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    sound_thread = threading.Thread(target=play_sound_rep, args=(mySound_file, volume,n_repeat, gap_time,rep_interval_cross_sound))
    mySound_rep = sound.Sound(mySound_file, preBuffer=-1, volume=volume)
    # mySound_rep.play()
    sound_thread.start()
    # -------Run Routine "trial"-------
    while continueRoutine:
        # get current time
        t = trialClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        if slider.markerPos and status[2] == 'down':
            continueRoutine=False
        elif slider.markerPos and t > ((mySound_rep.getDuration()+gap_time)*n_repeat + record_after + rep_interval_cross_sound):
            # break if sound stop
            continueRoutine=False   
        elif status[0] == 'down':
            sliding = -slider_granularity
        elif status[1] == 'down':
            sliding = slider_granularity
        # Move slider on hover
        elif slider_shape.contains(mouse) and mouse.getPos()[slider_orientation] != mouseRec[slider_orientation]:
            mouseRec = mouse.getPos()           
            relativeMousePos = (mouseRec[slider_orientation] / win.size[slider_orientation]) * 2 /slider_shape_width
            # hold the marker position if mouse move beyond the slider
            # if relativeMousePos < -1:
            #     relativeMousePos = slider_ticks[0]
            # elif relativeMousePos > 1:
            #     relativeMousePos = slider_ticks[-1]
            slider.markerPos = relativeMousePos * (slider_ticks[-1] - slider_ticks[0]) / 2 + (slider_ticks[0] + slider_ticks[-1]) / 2
            sliding = 0
        else:
            sliding = 0
        
        if sliding != 0:
            if oldRating == -1:
                slider.markerPos= (slider_ticks[0]+slider_ticks[-1])/2
            if frameN%slideSpeed == 0:
                slider.markerPos += sliding
        # Update slider text if needed
        if slider.markerPos:
            if oldRating != slider.markerPos:
                oldRating = slider.markerPos

        # record rating
        if slider.markerPos and frameN%slideSpeed==0:
            current_data = [round(oldRating, slider_decimals), int(t * 1000)]
            slider_data.append(current_data)	
        
        # *slider_shape* updates
        if slider_shape.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            slider_shape.frameNStart = frameN  # exact frame index
            slider_shape.tStart = t  # local t and not account for scr refresh
            slider_shape.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(slider_shape, 'tStartRefresh')  # time at next scr refresh
            slider_shape.setAutoDraw(True)
        
        # *slider* updates
        if slider.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            slider.frameNStart = frameN  # exact frame index
            slider.tStart = t  # local t and not account for scr refresh
            slider.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(slider, 'tStartRefresh')  # time at next scr refresh
            slider.setAutoDraw(True)
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in trialComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # -------Ending Routine "trial"-------
    for thisComponent in trialComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    print('All Responses',slider_data)
    print('Final Response',round(slider.markerPos,slider_decimals))
    print('slider.response', slider.getRating())
    print('slider.rt', slider.getRT())
    return slider, slider_data