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


class MouseReturnStates(IntEnum):
    unused = 0  # control/tool did not use the event.
    captured = 1  # control used the event and will use all future events until releasing.
    released = 2  # control used the event but is done using every event.


class GUIArtist(ABC):
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
    

class UIElement(GUIArtist, ABC):
    """
    Base class for UI elements (controls, tools, vectors).  UIElement objects can "capture" the mouse, i.e. use signals 
    differently depending on state.
    (For example, once drawing is started all control buttons are ignored (can be drawn under), or, if a control button is 
    currently pressed, no drawing can be done until the control button is released.)
    """

    def __init__(self, name, bbox, visible=True, pinned=True):
        """
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially
        :param pinned: bool, whether the control is pinned to the window (True) or moves/resizes with the board (False)
        """
        super().__init__(name, bbox)
        self.visible = visible
        self._pinned = pinned
        self._has_mouse = False

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        Handle mouse events, callback from cv2 or parent UIElement.
        NOTE:  UIElements are responsible for checking if the mouse is in their bounding box (if relevant).
        :returns: MouseReturnStates state as appropriate, 
        """
        pass

    def _release_mouse(self):
        # convenience function for mouse_event implementations
        # useful for UIElement types that take mouse signals from outisde their BBOX by "capturing" the mouse
        self._has_mouse = False
        return MouseReturnStates.released

    def _capture_mouse(self):
        # convenience function for mouse_event implementations
        self._has_mouse = True
        return MouseReturnStates.captured

    
class UIManager(UIElement, ABC):
    """
    Base class for objects that manage multiple UIElements of the same type.
    UIManagers have no visible respresentation, only their elements.
    """
    def __init__(self,  board, name, bbox, visible=True):
        super().__init__(name, bbox, visible, pinned = False)
        self._elements = []
        self._board=board
        self._init_elements()

    @abstractmethod
    def _init_elements(self):
        """
        Initialize whatever UIElements this class manages.
        """
        pass

    def render(self, img):
        """
        Render all UIElements that should be visible.
        """
        if not self._visible:
            return
        for element in self._elements:
            element.render(img)



class UIWindow(UIElement):
    """
    Base class for windows.
    """

    def __init__(self, board, window_name, window_size, visible=True,
                  win_params=cv2.WINDOW_NORMAL, bkg_color_n = 'off_white'):
        self._color_v = COLORS_BGR[bkg_color_n]
        self._frame = None  # current frame, need to redraw if None.
        self._blank = (np.zeros((window_size[1], window_size[0], 3))+ self._color_v).astype(dtype=np.uint8) 
        self._window_size = window_size
        self._win_params = win_params
        bbox = {'x': (0, window_size[0]), 'y': (0, window_size[1])}
        self._board=board

        super().__init__(window_name, bbox, visible, pinned=False)
        self._init_win()

    def _init_win(self):
        
        cv2.namedWindow(self.name, self._win_params)
        cv2.resizeWindow(self.name, self._bbox['x'][1], self._bbox['y'][1])
        cv2.setMouseCallback(self.name, self.mouse_event)

    
    def refresh(self):
        frame = self._blank.copy()
        self.render(frame)
        cv2.imshow(self.name, self._frame)

    def render(self, img):
        pass
    