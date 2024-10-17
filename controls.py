
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox
from gui_components import UIElement, UIManager


class Control(UIElement):
    """
    Abstract class for a thing you can interact with on the window that isn't the board.
    """

    def __init__(self, board, name, bbox, visible=True):
        """
        :param board: a Board object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially
        """
        super().__init__(name, bbox, visible)
        self._board = board
        self._moused_over = False
        # self._held = self._has_mouse
        self._active_window_name = None

    @abstractmethod
    def _set_geom(self):
        # called after move_to (may be useful in sublcasses' __init__ as well)
        pass

    @abstractmethod
    def render(self, img, show_bbox=True):
        # Draw the control on the image
        pass

    @abstractmethod
    def mouse_down(self, xy,  window_name):
        """
        Control doesn't have mouse, user clicked in self._bbox, control captures the mouse.
        """
        pass

    @abstractmethod
    def mouse_up(self, xy, window_name):
        """
        Control has mouse, user released mouse anywhere in the window.
        """
        pass

    def mouse_over(self, window_name):
        """
        Called when user moved the mouse into the control bbox.
        Control may or may not have the mouse.
        """
        pass

    def mouse_out(self, window_name):
        """
        Called whne user moved the mouse out of the control bbox.
        Control may or may not have the mouse.
        """
        pass

    @abstractmethod
    def mouse_move(self, xy,  window_name):
        """
        Control has mouse, user released mouse anywhere in the window.
        """
        pass

    def mouse_event(self, event, x, y, flags, param):
        # Controls use the above three methods
        pass

    def set_mouseover(self, moused_over):
        self._moused_over = moused_over

    def in_bbox(self, xy_px):
        if self._bbox is None:
            return True
        return in_bbox(self._bbox, xy_px)

    def move_to(self, xy, new_bbox=None):
        if new_bbox is None:
            self._bbox = {'x': (xy[0], xy[0] + self._bbox['x'][1] - self._bbox['x'][0]),
                          'y': (xy[1], xy[1] + self._bbox['y'][1] - self._bbox['y'][0])}
        else:
            self._bbox = new_bbox
        self._set_geom()


class ControlManager(UIManager):
    """
    Manages all UI controls (buttons, sliders, the ZoomWindow).

    """

    def __init__(self, board, controls):
        super().__init__(board, 'Control Manager', None, visible=False)

    def render(self, img):
        for control in self._controls:
            control.render(img)

    def mouse_event(self, event, xy, win_name):