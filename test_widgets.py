import cv2
import numpy as np
from slider import Slider
from layout import COLORS_RGB
from gui_components import MouseReturnStates
import logging
from controls import Button
class ControlTester(object):

    # fake app + canvas
    def __init__(self, win_size, controls):
        self._win_size = win_size
        self._bkg_color = COLORS_RGB['black']

        self._blank_frame = np.zeros((win_size[1], win_size[0], 3), dtype=np.uint8)
        self._blank_frame[:] = self._bkg_color
        self._win_name = 'Control Tester'
        self._controls = controls

        self._control_with_mouse = None

        cv2.namedWindow(self._win_name)
        cv2.setMouseCallback(self._win_name, self.mouse_event)
        while True:
            frame = self.render()
            cv2.imshow(self._win_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    def mouse_event(self, event, x, y, flags, param):
        if self._control_with_mouse is not None:
            rv = self._control_with_mouse.mouse_event(event, x, y, flags, param)
            if rv == MouseReturnStates.released:
                self._control_with_mouse = None
                logging.info("Mouse released by control %s" % self._control_with_mouse)
        else:
            for control in self._controls:
                rv =control.mouse_event(event, x, y, flags, param)
                if rv == MouseReturnStates.captured:
                    self._control_with_mouse = control
                    logging.info("Mouse captured by control %s" % control)
                elif rv == MouseReturnStates.released:
                    logging.info("Mouse used by control %s" % control)
                    break  # used but not captured


    def render(self):

        frame = np.zeros((self._win_size[1], self._win_size[0], 3), dtype=np.uint8)
        for control in self._controls:
            control.render(frame)
        return frame


def test_sliders():
    """
    One vertical and one horizontal.
    """
    width = 40
    length = 300

    s1 = {'bbox': {'x': (100, 100 + width), 'y': (150, 150 + length)},
          'label': 'Vertical',
          'orientation': 'vertical',
          'values': [1, 100],
          'visible': True,
          'interpolate': True,
          'init_pos': 0.5}
    s2 = {'bbox': {'x': (150, 150 + length), 'y': (100, 100 + width)},
          'label': 'Horizontal',
          'visible': True,
          'orientation': 'horizontal',
          'values': ['a', 'b', 'c', 'd', 'e'],
          'interpolate': False,
          'init_pos': 0.5}
    b1 = Button(None, 'Button', {'x': (20, 125), 'y': (100, 128)})

    slider1 = Slider(None, **s1)
    slider2 = Slider(None, **s2)
    ControlTester((500, 500), [slider1,slider2,b1])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # import ipdb;ipdb.set_trace()
    test_sliders()
