

from psychopy import visual, core, event

# Setup window
win = visual.Window(fullscr=False, size=[1024, 768], color='black')
mouse = event.Mouse(win=win)
mouse.mouseClock = core.Clock()

# Define upright triangle shape manually
triangle_vertices = [(0, 0.5), (-0.5, -0.5), (0.5, -0.5)]
tri_size = (0.4, 0.2)

# --- NAP (Left) Buttons ---
Nap_1 = visual.ShapeStim(win=win, name='NAP_1',
    vertices=triangle_vertices, size=tri_size, ori=135,
    pos=(-0.25, -0.175), lineColor='white', fillColor=[0.2, 0.2, 0.8], interpolate=True)

Nap_2 = visual.ShapeStim(win=win, name='NAP_2',
    vertices=triangle_vertices, size=tri_size, ori=315,
    pos=(-0.25, -0.035), lineColor='white', fillColor=[0.2, 0.2, 0.8], interpolate=True)

Nap_3 = visual.ShapeStim(win=win, name='NAP_3',
    vertices=triangle_vertices, size=tri_size, ori=225,
    pos=(-0.25, 0.035), lineColor='white', fillColor=[0.2, 0.2, 0.8], interpolate=True)

Nap_4 = visual.ShapeStim(win=win, name='NAP_4',
    vertices=triangle_vertices, size=tri_size, ori=45,
    pos=(-0.25, 0.175), lineColor='white', fillColor=[0.2, 0.2, 0.8], interpolate=True)

# --- WAKE (Right) Buttons ---
Wake_1 = visual.ShapeStim(win=win, name='WAKE_1',
    vertices=triangle_vertices, size=tri_size, ori=135,
    pos=(0.25, -0.175), lineColor='white', fillColor=[0.0, 0.6, 0.2], interpolate=True)

Wake_2 = visual.ShapeStim(win=win, name='WAKE_2',
    vertices=triangle_vertices, size=tri_size, ori=315,
    pos=(0.25, -0.035), lineColor='white', fillColor=[0.0, 0.6, 0.2], interpolate=True)

Wake_3 = visual.ShapeStim(win=win, name='WAKE_3',
    vertices=triangle_vertices, size=tri_size, ori=225,
    pos=(0.25, 0.035), lineColor='white', fillColor=[0.0, 0.6, 0.2], interpolate=True)

Wake_4 = visual.ShapeStim(win=win, name='WAKE_4',
    vertices=triangle_vertices, size=tri_size, ori=45,
    pos=(0.25, 0.175), lineColor='white', fillColor=[0.0, 0.6, 0.2], interpolate=True)

# --- List of buttons ---
grid_buttons = [
    {'name': 'NAP_1', 'button': Nap_1},
    {'name': 'NAP_2', 'button': Nap_2},
    {'name': 'NAP_3', 'button': Nap_3},
    {'name': 'NAP_4', 'button': Nap_4},
    {'name': 'WAKE_1', 'button': Wake_1},
    {'name': 'WAKE_2', 'button': Wake_2},
    {'name': 'WAKE_3', 'button': Wake_3},
    {'name': 'WAKE_4', 'button': Wake_4},
    {'name': 'NO', 'button': NO_button}
]

# --- Main draw-and-click loop ---
selected_response = None
mouse.clickReset()

while selected_response is None:
    # Draw all components
    text_question.draw()
    text_certain.draw()
    text_uncertain.draw()
    text_NAP.draw()
    text_WAKE.draw()

    for item in grid_buttons:
        item['button'].draw()
    text_NO.draw()

    win.flip()

    if mouse.getPressed()[0]:
        for item in grid_buttons:
            if item['button'].contains(mouse):
                selected_response = item['name']
                click_pos = mouse.getPos()
                rt = mouse.mouseClock.getTime()
                break
        core.wait(0.2)

# --- Print/log result ---
print(f"Selected: {selected_response}, Pos: {click_pos}, RT: {rt}")
trial_data = {
    'response': selected_response,
    'click_x': click_pos[0],
    'click_y': click_pos[1],
    'rt': rt
}
