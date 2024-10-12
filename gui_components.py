"""
Define some lightweight UI elements for the app.
"""
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from layout import COLORS_RGB
import logging
from enum import IntEnum
from util import in_bbox


class MouseReturnStates(IntEnum):
    unused = 0  # control/tool did not use the event.
    captured = 1  # control used the event and will use all future events until releasing.
    released = 2  # control used the event but is done using every event.


class UIWindow(ABC):
    """
    Base class for windows.
    """

    def __init__(self, window_size, window_name):
        self._window_size = window_size
        self._window_name = window_name
        self._frame = None  # current frame, need to redraw if None.

        self._elements = []  # list of UIElement objects on the canvas, UI buttons, tools, etc.
        self._element_with_mouse = None 
        # index into self._elements (e.g. pencil, select):

        self._current_tool = None  # NOTE: self._elements[self._current_tool] should always be a Tool object.
        self._init_elements()

    @abstractmethod
    def _init_elements(self):
        """
        Initialize UIElement objects, things that are drawn on the window (toolboxes, etc),
        things that can change the canvas (pencil, pen, etc.)
        """
        pass

    @abstractmethod
    def _render(self):
        """
        Render the current state into an image with size self._window_size.
        """
        pass

    @abstractmethod
    def mouse_callback(self, event, x, y, flags, param):
        """
        CV2 mouse callback function.
        """
        pass

    def get_frame(self):
        if self._frame is None:
            self._frame = self._render()
        return self._frame


class UIElement(ABC):
    """
    Category of UI elements that can capture mouse events once activated.
    (For example, once drawing is started, buttons are ignored, and control button is pressed,
    no drawing can be done until the control button is released.)
    """
    def __init__(self, canvas, name, bbox, visible=True, pinned=True):
        """
        :param canvas: a Canvas object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially
        :param pinned: bool, whether the control is pinned to the window (True) or moves/resizes with the canvas (False)
        """
        self._name = name
        self._bbox = bbox
        self._canvas = canvas
        self._visible = visible
        self._pinned = pinned
        self._has_mouse = False 

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        Handle mouse events.
        :returns: MouseReturnStates state as appropriate, 
        """
        pass

    def _release_mouse(self):
        # convenience function for mouse_event implementations
        self._has_mouse = False
        return MouseReturnStates.released
    
    def _capture_mouse(self):
        # convenience function for mouse_event implementations
        self._has_mouse = True
        return MouseReturnStates.captured

    @abstractmethod
    def render(self, img):
        pass

    @abstractmethod
    def in_bbox(self, xy):
        """
        Check if the point is in the bounding box.
        Return none if this element doesn't have a bounding box (e.g. tools).
        """
        pass

class CanvasView(object):
    """
    Represents the view of the canvas in the window.
    """
    def __init__(self, size, origin, zoom):
        self.origin = origin
        self.zoom = zoom
        self.size = size

    def screen_to_canvas(self, xy):
        xy = np.array(xy)
        return (xy - self.origin) / self.zoom
    
    def canvas_to_screen(self, xy):
        xy = np.array(xy)
        return xy * self.zoom + self.origin
