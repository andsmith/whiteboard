
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox
from gui_components import UIElement, MouseReturnStates, UIManager



class Control(UIElement):
    """
    Abstract class for a thing you can interact with on the window that isn't the board.
    """

    def __init__(self, board, name, bbox, visible=True, pinned=True):
        """
        :param board: a Board object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially
        :param pinned: bool, whether the control is pinned to the window (True) or moves/resizes with the board (False)
        """
        super().__init__( name, bbox, visible, pinned)
        self._board = board

    @abstractmethod
    def _set_geom(self):
        # called after move_to (may be useful in sublcasses' __init__ as well)
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

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        :return: MouseReturnStates
        """
        pass

    @abstractmethod
    def render(self, img, show_bbox=True):
        pass

class ControlManager(UIManager):
    """
    Manages set of controls on the board.
    """

    def __init__(self, board):
        super().__init__(board, 'Control Manager', None, visible=False, pinned=True)
        self._controls = []

    def _init_elements(self):
        # Toolbox (in control window)
        # colorbox (in control window)
        # zoom window (in board window)
        # zoom slider bar (in control window)
        # zoom slider bar (in board window)
        pass
    
    def render(self, img):
        for control in self._controls:
            control.render(img)
