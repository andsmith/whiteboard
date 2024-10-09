
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox
from gui_components import UIElement


class Widget(UIElement):
    """
    Abstract class for all UI components (things you can interact with on the window)
    """

    def __init__(self, canvas, bbox, visible=True, pinned=True):
        """
        :param canvas: a Canvas object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the widget is visible initially
        :param pinned: bool, whether the widget is pinned to the window (True) or moves/resizes with the canvas (False)
        """
        self._bbox = bbox
        self._canvas = canvas  
        self._visible = visible
        self._pinned = pinned

    def in_bbox(self, xy_px):
        if self._bbox is None:
            return True
        return in_bbox(self._bbox, xy_px)
    
    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        :return: MouseReturnStates
        """
        pass

    @abstractmethod
    def render(self, img, show_bbox=True):
        pass
