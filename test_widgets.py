import cv2
import numpy as np
from slider import Slider
from layout import COLORS_RGB
from gui_components import MouseReturnStates
import logging

class WidgetTester(object):
    # fake app + canvas
    def __init__(self, win_size, widgets):
        self._win_size = win_size
        self._bkg_color = COLORS_RGB['black']

        self._blank_frame = np.zeros((win_size[1], win_size[0], 3), dtype=np.uint8)
        self._blank_frame[:] = self._bkg_color
        self._win_name = 'Widget Tester'
        self._widgets = widgets

        self._widget_with_mouse = None

        cv2.namedWindow(self._win_name)
        cv2.setMouseCallback(self._win_name, self.mouse_event)
        while True:
            frame = self.render()
            cv2.imshow(self._win_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    def mouse_event(self, event, x, y, flags, param):
        print(self._widget_with_mouse)
        if self._widget_with_mouse is not None:
            rv, _ = self._widget_with_mouse.mouse_event(event, x, y, flags, param)
            if rv == MouseReturnStates.released:
                self._widget_with_mouse = None
                print("!")
                logging.info("Mouse released by widget %s" % self._widget_with_mouse)
        else:
            for widget in self._widgets:
                if widget.in_bbox((x, y)):
                    rv, _=widget.mouse_event(event, x, y, flags, param)
                    if rv == MouseReturnStates.captured:
                        self._widget_with_mouse = widget
                        logging.info("Mouse captured by widget %s" % widget)
                    elif rv == MouseReturnStates.released:
                        logging.info("Mouse used by widget %s" % widget)
                        break  # used but not captured
                    else:
                        logging.info("Mouse not used by widget %s" % widget)


    def render(self):

        frame = np.zeros((self._win_size[1], self._win_size[0], 3), dtype=np.uint8)
        for widget in self._widgets:
            widget.render(frame)
        return frame


def test_sliders():
    """
    One vertical and one horizontal.
    """
    width = 20
    length = 300

    s1 = {'bbox': {'x': (100, 100 + width), 'y': (100, 100 + length)},
          'label': 'Vertical',
          'orientation': 'vertical',
          'values': [1, 100],
          'interpolate': True,
          'init_pos': 0.5}
    s2 = {'bbox': {'x': (150, 150 + length), 'y': (100, 100 + width)},
          'label': 'Horizontal',
          'orientation': 'horizontal',
          'values': ['a', 'b', 'c', 'd', 'e'],
          'interpolate': False,
          'init_pos': 0.5}
    slider1 = Slider(None, **s1)
    slider2 = Slider(None, **s2)
    WidgetTester((500, 500), [slider1,slider2])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # import ipdb;ipdb.set_trace()
    test_sliders()
