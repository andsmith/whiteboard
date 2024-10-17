"""
The Zoom windows are two special controls represented by a rectangle in both windows.
They outline the same region of the board, i.e. one is a zoomed-in view of the other at all times.

The ZoomViewControl is in the BoardWindow, can be moved by dragging or resized by dragging 
a resize icon in one of the corners.

The ZoomDrawControl is in the ControlWindow, mouse actions within it's BBOX go to the current tool for drawing,
(which is the default behavior in the BoardWindow).  Moving the mouse after clicking somewhere outside the bbox
pans the views of the board (in both windows).  Resizing this just affects which part of the window can be used 
for drawing.  

"""
import numpy as np
from controls import Control
from util import corners_to_bbox, move_bbox_to


class BoardBBox(object):
    """
    Represents actuall bbox of the zoom windows in booard-coordinates.
    """

    def __init__(self, x_span, y_span):
        self._bbox = {'x': x_span,
                      'y': y_span}

        self._pan_offset = None  # user is panning (in either window)

        # The Control objects, move them when self moves:
        self._view = None
        self._draw = None

    def makeZoomViewControl(self, board, board_view):
        view_bbox = self.get_win_coords(board_view)
        self._view = ZoomViewControl(board, view_bbox, self)

    def makeZoomDrawControl(self, board, board_view):
        view_bbox = self.get_win_coords(board_view)
        self._draw = ZoomDrawControl(board, view_bbox, self)

    def get_win_bbox(self, board_view):
        """
        Return the window coordinates of the bbox.
        :param board_view: BoardView object
        :returns: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        """
        x_min = board_view.origin[0] + self._bbox['x'][0]
        x_max = board_view.origin[0] + self._bbox['x'][1]
        y_min = board_view.origin[1] + self._bbox['y'][0]
        y_max = board_view.origin[1] + self._bbox['y'][1]

        x_min_w, y_min_w = board_view.to_win_coords((x_min, y_min))
        x_max_w, y_max_w = board_view.to_win_coords((x_max, y_max))
        return {'x': (x_min_w, x_max_w), 'y': (y_min_w, y_max_w)}

    def move_to(self, xy, new_bbox=None):
        """
        Set the new origin/boundaries of the bbox.
        """
        # new bbox in board coordinates:
        self._bbox = new_bbox if new_bbox is not None else move_bbox_to(self._bbox, xy)

        # view coords
        view_bbox = self.get_win_coords(self._view)
        


class ZoomViewControl(Control):
    def __init__(self, board, bbox, region):
        name = 'Zoom View Control'
        super().__init__(board, name, bbox, True)
        self._region = region
        self._mousedown_pos = None
        self._panning = False
        self._resizing = False

    def mouse_down(self, xy, window_name):
        self._mousedown_pos = xy
        if self._in_resize_corner(xy):
            self._resizing = True
            return self._capture_mouse()
        else:
            self._panning = True
            return self._capture_mouse()

    def mouse_up(self, xy, window_name):
        self._panning = False
        self._resizing = False
        return self._release_mouse()

    def mouse_move(self, xy, window_name):
        if self._panning:
            self._pan(xy)
        elif self._resizing:
            self._resize(xy)
        return self._capture_mouse()


class ZoomDrawControl(Control):
    def __init__(self, board, bbox):
        name = 'Zoom Draw Control'
        super().__init__(board, name, bbox, True)

    def mouse_down(self, xy, window_name):
        self._activate()
        return self._capture_mouse()

    def mouse_up(self, xy, window_name):
        self._activate()
        return self._release_mouse()

    def mouse_move(self, xy, window_name):
        if self._has_mouse:
            self._activate()
        return self._capture_mouse()
