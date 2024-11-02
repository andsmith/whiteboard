import cv2
import numpy as np
from slider import Slider
from layout import COLORS_BGR, CONTROL_LAYOUT, EMPTY_BBOX, COLOR_BUTTONS, BOARD_LAYOUT
from gui_components import MouseReturnStates
import logging
from buttons import Button, ColorButton, ToolButton
from button_box import ButtonBox

TEST_COLORS = CONTROL_LAYOUT['color_box']['options']
TEST_TOOLS = CONTROL_LAYOUT['tool_box']['options']

class FakeToolManager(object):
    def __init__(self):
        pass

    def set_color(self, color):
        logging.info("Setting color to %s" % color)

    def switch_tool(self, tool):
        logging.info("Setting tool to %s" % tool)

    def get_color_thickness(self):
        return 'orange', 3


class ControlTester(object):

    # fake app + board
    def __init__(self, win_size):
        self._win_size = win_size
        self.default_color_v = COLORS_BGR[BOARD_LAYOUT['obj_color']]
        self._bkg_color_v = COLORS_BGR[BOARD_LAYOUT['bkg_color']]
        self.tools = FakeToolManager()
        self._blank_frame = np.zeros((win_size[1], win_size[0], 3), dtype=np.uint8)
        self._blank_frame[:] = self._bkg_color_v
        self._win_name = 'Control Tester'
        self._controls = None
        self._control_with_mouse = None


    def add_widgets(self, widgets):
        self._controls = widgets
        

    def run(self):
        cv2.namedWindow(self._win_name)
        cv2.setMouseCallback(self._win_name, self.mouse_event)
        while True:
            if not self.render_and_show():
                break

    def render_and_show(self, delay=1):
        frame = self.render()
        cv2.imshow(self._win_name, frame)
        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            return False
        return True

    def mouse_event(self, event, x, y, flags, param):
        if self._control_with_mouse is not None:
            rv = self._control_with_mouse.mouse_event(event, x, y, flags, param)
            if rv == MouseReturnStates.released:
                self._control_with_mouse = None
                logging.info("Mouse released by control %s" % self._control_with_mouse)
        else:
            for control in self._controls:
                rv = control.mouse_event(event, x, y, flags, param)
                if rv == MouseReturnStates.captured:
                    self._control_with_mouse = control
                    logging.info("Mouse captured by control %s" % control)
                elif rv == MouseReturnStates.released:
                    # logging.info("Mouse used by control %s" % control)
                    break  # used but not captured

    def render(self):

        frame = self._blank_frame.copy()
        for control in self._controls:
            control.render(frame)
        return frame


def test_widgets():
    """
    Widget sandbox.
    """
    width = 40
    length = 300

    # sliders
    s1 = {'bbox': {'x': (10, 110 + width), 'y': (150, 150 + length)},
          'name': 'Vertical',
          'orientation': 'vertical',
          'values': [1, 100],
          'visible': True,
          'interpolate': True,
          'init_pos': 0.5}
    s2 = {'bbox': {'x': (150, 150 + length), 'y': (100, 100 + width)},
          'name': 'Horizontal',
          'visible': True,
          'orientation': 'horizontal',
          'values': ['a', 'b', 'c', 'd', 'e'],
          'interpolate': False,
          'init_pos': 0.5}
    slider1 = Slider(None, **s1)
    slider2 = Slider(None, **s2)

    ct = ControlTester((500, 500))
    # single button, true-false
    b1 = Button(ct, 'Button', {'x': (20, 125), 'y': (100, 128)})

    # button box, radio-button style
    buttons = [Button(ct, '%s' % (lab,), None, ) for lab in ['a', 'b', 'c', 'd', 'e']]
    button_grid = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # 3 row and 2 col grid.
    bbx1 = ButtonBox(ct, 'exclusive_button_box', {'x': (160, 290), 'y': (
        190, 280)}, button_grid, exclusive=True, exclusive_init=buttons[1])

    # button box, (collection of unconstrained buttons)
    buttons = [Button(ct, '%s' % (lab,), None, ) for lab in ['1', '2', '3', '4', '5', '6']]
    button_grid = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # 3 row and 2 col grid.
    bbx2 = ButtonBox(ct, 'button_box', {'x': (300, 430), 'y': (190, 280)}, button_grid, exclusive=False)

    # color button

    b2 = ColorButton(ct, 'Color Button', {'x': (20, 80), 'y': (20, 80)}, 'orange')

    # Color button box
    color_buttons = [[ColorButton(ct, "CB: %s" % (color_name,), EMPTY_BBOX, color_name)
                      for color_name in row]
                     for row in TEST_COLORS]
    bbx3 = ButtonBox(ct, 'color_button_box', {'x': (170, 260), 'y': (300, 480)}, color_buttons, exclusive=True)

    # Tool button box

    tool_buttons = [[ToolButton(ct, tool_name, EMPTY_BBOX) for tool_name in row] for row in TEST_TOOLS]
    
    bbx4 = ButtonBox(ct, 'tool_button_box', {'x': (300, 430), 'y': (300, 480)}, tool_buttons, exclusive=True)

    ct.add_widgets( [slider1, slider2, b1, bbx1, bbx2, b2, bbx3, bbx4])
    ct.run()

    return

    def _get_center(bbox):
        return (bbox['x'][0] + bbox['x'][1]) // 2, (bbox['y'][0] + bbox['y'][1]) // 2
    button_centers = {button.name: _get_center(button.get_bbox()) for button in buttons}

    events = [{'label': 'mouseover button d', 'kwargs': {'event': cv2.EVENT_MOUSEMOVE, 'x': button_centers['d'][0], 'y': button_centers['d'][1], 'flags': 0, 'param': None}},
              {'label': 'mouseover button c', 'kwargs': {'event': cv2.EVENT_MOUSEMOVE,
                                                         'x': button_centers['c'][0], 'y': button_centers['c'][1], 'flags': 0, 'param': None}},
              {'label': 'click button d', 'kwargs': {'event': cv2.EVENT_LBUTTONDOWN,
                                                     'x': button_centers['d'][0], 'y': button_centers['d'][1], 'flags': 0, 'param': None}},
              {'label': 'release button d', 'kwargs': {'event': cv2.EVENT_LBUTTONUP,
                                                       'x': button_centers['d'][0], 'y': button_centers['d'][1], 'flags': 0, 'param': None}},
              {'label': 'click button c', 'kwargs': {'event': cv2.EVENT_LBUTTONDOWN,
                                                     'x': button_centers['c'][0], 'y': button_centers['c'][1], 'flags': 0, 'param': None}},
              {'label': 'release button c', 'kwargs': {'event': cv2.EVENT_LBUTTONUP,
                                                       'x': button_centers['c'][0], 'y': button_centers['c'][1], 'flags': 0, 'param': None}},
              ]
    import ipdb
    ipdb.set_trace()

    for event in events:
        logging.info("Sending event %s" % event['label'])
        t.mouse_event(**event['kwargs'])
        t.render_and_show(1000)
    t.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_widgets()
