
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox
from gui_components import Renderable, MouseReturnStates


class Control(Renderable):
    """
    Abstract class for a thing you can interact with on the window that isn't the board.

     MouseManagers get cv2 mouse events, decide which Control & method to call.

    Interactables never need to check their own bounding box (MouseManagers do that).

    """

    def __init__(self, window, name, bbox, visible=True):
        """
        :param window: a UIWindow object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially        
        """
        super().__init__(name, bbox)
        self.visible = visible
        self._has_mouse = False
        self._window = window
        self._moused_over = False
        self._set_geom()

    @abstractmethod
    def mouse_down(self, xy):
        """
        Control doesn't have mouse, user clicked in self._bbox, control captures the mouse.
        :returns: MouseReturnStates
        """
        pass

    @abstractmethod
    def mouse_up(self, xy):
        """
        Control has mouse, user released mouse anywhere in the window.
        :returns: MouseReturnStates
        """
        pass

    @abstractmethod
    def mouse_move(self, xy):
        """
        Control has mouse, user released mouse anywhere in the window.
        :returns: MouseReturnStates
        """
        pass

    def mouse_over(self, xy):
        """
        Called when user moved the mouse into the control bbox.
        Control may or may not have the mouse.
        """
        self._moused_over = True

    def mouse_out(self, xy):
        """
        Called when user moved the mouse out of the control bbox.
        Control may or may not have the mouse.
        """
        self._moused_over = False

    def _release_mouse(self):
        # convenience function for mouse_event implementations
        # useful for UIElement types that take mouse signals from outisde their BBOX by "capturing" the mouse
        self._has_mouse = False
        return MouseReturnStates.released

    def _capture_mouse(self):
        # convenience function for mouse_event implementations
        self._has_mouse = True
        return MouseReturnStates.captured

    @abstractmethod
    def _set_geom(self):
        # called in __init__ and  move_to 
        pass

    @abstractmethod
    def render(self, img):
        # Draw the control on the image
        pass

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
