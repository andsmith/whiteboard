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
                  win_params=cv2.WINDOW_NORMAL, bkg_color = 'off_white'):
        self._color = COLORS_RGB[bkg_color]
        self._frame = None  # current frame, need to redraw if None.
        self._blank = np.zeros((window_size[1], window_size[0], 3), dtype=np.uint8) + self._color
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
    

class BoardView(object):
    """
    Represents the view of some part of the board (the cartesian plane).
    """

    def __init__(self, size, origin, zoom):
        self.origin = origin  # upper left pixel in the view has this position in the board.
        self.zoom = zoom  # pixels per board unit
        self.size = size  # size of the view in pixels (w x h)

        # bounding box of this view within the board, in board coords.
        self.board_bbox = {'x': (origin[0], origin[0] + size[0] / zoom),  
                           'y': (origin[1], origin[1] + size[1] / zoom)}

    def from_new_size(self, new_size):
        """
        Create a new view with the new window size.
        When the aspect ratio changes, pick zoom level that inscribes the old view and is centered.
        """
        x_range = self.board_bbox['x'][1] - self.board_bbox['x'][0]
        y_range = self.board_bbox['y'][1] - self.board_bbox['y'][0]
        aspect = x_range / y_range
        new_aspect = new_size[0] / new_size[1]
        if new_aspect > aspect:
            # new window is wider, use height to determine zoom
            zoom = new_size[1] / y_range
            x_center = (self.board_bbox['x'][0] + self.board_bbox['x'][1]) / 2
            x_range = new_size[0] / zoom
            origin = (x_center - x_range / 2, self.board_bbox['y'][0])
        else:
            # new window is taller, use width to determine zoom
            zoom = new_size[0] / x_range
            y_center = (self.board_bbox['y'][0] + self.board_bbox['y'][1]) / 2
            y_range = new_size[1] / zoom
            origin = (self.board_bbox['x'][0], y_center - y_range / 2)
        return BoardView(new_size, origin, zoom)

    def pts_from_pixels(self, xy):
        xy = np.array(xy)
        return (xy / self.zoom) + self.origin

    def pts_to_pixels(self, xy):
        # flip y?
        xy = np.array(xy)
        xy_px = (xy - self.origin) * self.zoom
        return xy_px.astype(np.int32)
    
    def sees_bbox(self, bbox):
        """
        Returns True if the view sees any part of the bbox.
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)} in board coords.
        """
        return bboxes_intersect(self.board_bbox, bbox)
    


def get_board_view(points, win_size, margin=0.05):
    """
    Return a BoardView object that cointains all the points centered in it w/a margin.
    """
    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    # Determine if vertical hor horizontal padding is needed (beyond the margin).
    data_aspect = (x_max - x_min) / (y_max - y_min)
    view_aspect = win_size[0] / win_size[1]
    if data_aspect > view_aspect:
        # data is wider than view, add vertical padding
        y_range = (x_max - x_min) / view_aspect
        y_center = (y_max + y_min) / 2
        y_min = y_center - y_range / 2
        y_max = y_center + y_range / 2
    else:
        # data is taller than view, add horizontal padding
        x_range = (y_max - y_min) * view_aspect
        x_center = (x_max + x_min) / 2
        x_min = x_center - x_range / 2
        x_max = x_center + x_range / 2  


    x_range = x_max - x_min
    y_range = y_max - y_min
    x_margin = x_range * margin
    y_margin = y_range * margin
    origin = (x_min - x_margin, y_min - y_margin)
    size = (x_range + 2 * x_margin, y_range + 2 * y_margin)
    zoom = min(win_size[0] / size[0], win_size[1] / size[1])
    return BoardView(win_size, origin, zoom)