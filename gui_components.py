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
    subclasses: Control, IconArtist, Vector
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
