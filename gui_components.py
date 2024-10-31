"""
Define some lightweight UI elements for the app.
"""
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from layout import COLORS_BGR
import logging
from enum import IntEnum
from util import in_bbox, bboxes_intersect


MOUSE_SIGNAL_ORDER = ['control_manager', 'tool_manager']

RENDER_ORDER = ['vectors_m', 'controls', 'tools']


class Renderable(ABC):
    """
    Something that can draw in a bounding box within an image.
    """

    def __init__(self, name, bbox):
        """
        :param name: string, name of the artist
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}, ints or float.
        :param visible: bool, whether the artist should be
        """
        self.name = name
        self._bbox = bbox   # pixels within a window or board-coordinates, depending on subclass.

    @abstractmethod
    def render(self, img):
        """
        Draw control/tool-cursor/vector.
        """
        pass

    def in_bbox(self, xy):
        """
        Check if the point is in the bounding box.
        Return none if this element doesn't have a bounding box (e.g. tools) (?)
        """
        if self._bbox is None:
            return None
        return in_bbox(xy, self._bbox)

    def get_bbox(self):
        return self._bbox


class MouseReturnStates(IntEnum):
    unused = 0  # control/tool did not use the event.
    captured = 1  # control used the event and will use all future events until releasing.
    released = 2  # control used the event but is done using every event.

class MouseManager(ABC):
    """
    Base class for containing multiple Interactable objects, receiving CV2 mouse events, 
    Deciding which object gets the event, etc.
    """

    def __init__(self,   bbox, visible=True):
        self._bbox = bbox
        self._visible = visible
        self._interactables = self._get_interactables()

        self._element_with_mouse = None
        self._cur_xy = None
        self._click_xy = None
        self._moused_over_element = None

    def mouse_event(self, event, xy, view):
        """
        Mouse event in the control window:
            - Check if it's captured by a current tool/control.
            - Check all control panels.
            - Send to current tool.
        Also, set mouseover state correctly.
        :param event: cv2.EVENT_...
        :param xy: (x, y) tuple, coordinates within the window of the event.
        :param view: BoardView object (which includes the window that the event was in)
        """
        if self._element_with_mouse is not None:
            rv = self._element_with_mouse.mouse_event(event, xy, view)
            if rv == MouseReturnStates.released:
                self._element_with_mouse = None
        else:

            for element in self._controls:
                # Controls check if the mouse is in their bbox.
                rv = control.mouse_event(event,  xy, view)
                if rv == MouseReturnStates.captured:
                    self._element_with_mouse = control
                    return
        current_tool = self._board.get_current_tool()
        rv = current_tool.mouse_event(event, xy, view)
        if rv == MouseReturnStates.captured:
            self._element_with_mouse = current_tool

    def add_element(self, element):
        """
        :param element: UIElement object
        """
        self._elements.append(element)

    def render(self, img):
        """
        Render all UIElements that should be visible.
        """
        if not self._visible:
            return
        for element in self._elements:
            element.render(img)
