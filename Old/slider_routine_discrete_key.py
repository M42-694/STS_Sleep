# --- Import packages ---
from psychopy import prefs
from psychopy import plugins
from psychopy import core
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER, priority)
from psychopy.event import Mouse
from psychopy.hardware import keyboard


plugins.activatePlugins()
prefs.hardware['audioLib'] = ['sounddevice', 'PTB', 'pyo', 'pygame'] #'ptb'
prefs.hardware['audioLatencyMode'] = '0'
defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER, priority)
defaultKeyboard = keyboard.Keyboard(backend='psychotoolbox')

def slider_routine_discrete_key(win, slider, slider_shape, text_slider, text_data, 
                slider_orientation, slider_ticks, slider_granularity, slider_shape_width,
                   slider_decimals, slideSpeed, oldRating, text_above_slider, step_size,end_key_name):
    frameTolerance = 0.001  # how close to onset before 'same' frame
    trialClock = core.Clock()
    continueRoutine = True
    # a keyboard object (must differ from object used online)
    mykb = keyboard.Keyboard()

    if slider_granularity == 0:
        slider_granularity = .1
    thisFrame = 0
    if oldRating == None:
       oldRating = -1
        
    slider_data=[]
    text_data.text=''
    # which keys are we watching? (these will differ depending on handedness)
    keysWatched = ['left', 'right', 'down','return']
    # what are the assumed key statuses at the start of the routine
    status = {key: 'up' for key in keysWatched}  # Using a dictionary to track key states
    # how many keyPresses have been counted so far 
    slider.reset()
    
    # Set initial position of the slider if oldRating is specified
    if oldRating != -1:
        slider.markerPos = oldRating
        text_slider.text = str(round(oldRating, slider_decimals))
    else:
        slider.markerPos = (slider_ticks[0] + slider_ticks[-1]) / 2

    # keep track of which components have finished
    trialComponents = [slider_shape, slider, text_slider, text_data, text_above_slider]
    for thisComponent in trialComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    trialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "trial"-------
    while continueRoutine:
        # get current time
        t = trialClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        # poll the keyboard
        keys = mykb.getKeys(keysWatched, waitRelease=False, clear=False)
        
        sliding = 0  # Reset sliding to 0 at the beginning of each frame
        
        if len(keys) > 0:
            for key in keys:
                if key.name in ['left', 'right']:
                    if key.name == 'left':
                        sliding = -step_size
                    elif key.name == 'right':
                        sliding = step_size
                    # status[key.name] = 'down'
                elif key.name == end_key_name:
                    continueRoutine = False
        
        # Reset status to 'up' if the key is released
        # for key in keysWatched:
        #     if key not in [k.name for k in keys]:
        #         status[key] = 'up'
        
        if sliding != 0:
            if oldRating == -1:
                slider.markerPos = (slider_ticks[0] + slider_ticks[-1]) / 2
            if thisFrame % slideSpeed == 0:
                slider.markerPos += sliding
        
        # Update slider text if needed
        if slider.markerPos:
            if oldRating != slider.markerPos:
                text_slider.text = str(round(slider.markerPos, slider_decimals))
                oldRating = slider.markerPos
        
        if slider.markerPos and thisFrame % slideSpeed == 0:
            slider_data.append([round(oldRating, slider_decimals), int(t * 1000)])
            text_data.pos = [.6, -.4 + .017 * len(slider_data)]
            text_data.text += '\n' + str(round(oldRating, slider_decimals)) + ' ' + str(int(t * 1000))
        
        # *slider_shape* updates
        if slider_shape.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            slider_shape.frameNStart = frameN  # exact frame index
            slider_shape.tStart = t  # local t and not account for scr refresh
            slider_shape.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(slider_shape, 'tStartRefresh')  # time at next scr refresh

        # *text_above_slider* updates
        if text_above_slider.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            text_above_slider.frameNStart = frameN  # exact frame index
            text_above_slider.tStart = t  # local t and not account for scr refresh
            text_above_slider.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(text_above_slider, 'tStartRefresh')  # time at next scr refresh
            text_above_slider.setAutoDraw(True)
        
        # *slider* updates
        if slider.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            slider.frameNStart = frameN  # exact frame index
            slider.tStart = t  # local t and not account for scr refresh
            slider.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(slider, 'tStartRefresh')  # time at next scr refresh
            slider.setAutoDraw(True)
        
        # *text_slider* updates
        if text_slider.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            text_slider.frameNStart = frameN  # exact frame index
            text_slider.tStart = t  # local t and not account for scr refresh
            text_slider.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(text_slider, 'tStartRefresh')  # time at next scr refresh
            text_slider.setAutoDraw(True)
        
        # *text_data* updates
        if text_data.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            text_data.frameNStart = frameN  # exact frame index
            text_data.tStart = t  # local t and not account for scr refresh
            text_data.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(text_data, 'tStartRefresh')  # time at next scr refresh
            text_data.setAutoDraw(True)
        
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
    print('All Responses', slider_data)
    print('Final Response', round(slider.markerPos, slider_decimals))
    print('slider.response', slider.getRating())
    print('slider.rt', slider.getRT())
    
    return slider, slider_data