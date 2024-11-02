"""
Class to represent simple vector drawing shapes.
"""
from gui_components import Renderable
import cv2

import numpy as np
from layout import COLORS_BGR, VECTOR_DEF, EMPTY_BBOX
from abc import ABC, abstractmethod
from util import get_bbox, PREC_BITS,PREC_SCALE, floats_to_fixed, get_circle_points
import json
import time


class Vector(Renderable, ABC):
    """
    Base class for vectors, all defined by a user input consisting of a sequence of points.
    Vectors represent some change to the board, e.g., line, circle, pencil stroke.

    When objects are first created, or when selected, they are 'unfinalized' (i.e. in progress).
    Unfinalized/highlighted objects may be drawn differently.
    Objects are finalized when the user releases the mouse button (etc.).
    """

    def __init__(self, color, thickness):
        """
        :param board: Board object
        :param color: (r, g, b) tuple or string
        :param thickness: int
        """
        self._highlight_level = 0  # 0 = no highlight, 1 = selected  (TODO: 2 = hovered, 3 = ?, ...)
        self._finalized_t = None  # time when the vector was finalized, in epoch.
        self._color = COLORS_BGR[color] if isinstance(color, str) else tuple(color)
        self._thickness = thickness
        self._points = []

        super().__init__(self.__class__.__name__, EMPTY_BBOX)

    def __eq__(self, other):
        # compare timestamps?
        equal = self._color == other._color and \
              self._thickness == other._thickness and \
              np.isclose(self._points, other._points).all()
        return equal

    @abstractmethod
    def get_data(self):
        """
        Return the data needed to serialize this vector (must be JSON-able).
        """
        pass

    @staticmethod
    @abstractmethod
    def from_data(string):
        """
        Return a new vector object from the data (as returned by get_data).
        """
        pass

    @abstractmethod
    def render(self, img, view):
        """
        Draw the vector on the image, or whatever part is in bounds.
        :param img: np.array, image to draw on.
        :param view:  a BoardView object, the portion of the board that is visible in this image.
        """
        pass

    def finalize(self):
        self._finalized_t = time.time()

    def add_point(self, xy, view=None):
        """
        User moved the mouse, add the new point.
        :param xy: the point to add, assumed to be pixel coords (ints) if view is not None, else board coords (floats).
        :param view: BoardView object
        """
        xy_board = view.pts_from_pixels(xy) if view is not None else xy
        self._points.append(xy_board)
        self._bbox = get_bbox(self._points)

    def get_data(self):
        if self._finalized_t is None:
            raise ValueError("Vector not finalized, don't serialize!")

        data = {'color': self._color,
                'thickness': self._thickness,
                'points': np.array(self._points).tolist(),
                'timestamp': self._finalized_t}
        return data

    @classmethod
    def from_data(cls, data):
        r = cls(data['color'], data['thickness'])
        r._points = data['points']
        r._bbox = get_bbox(r._points)
        r._finalized_t = data['timestamp']
        return r


class PencilVec(Vector):
    """
    Pencil stroke connects the sequence of points a line that has the given properties.
    """
    _NAME = 'pencil'
    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            coords = [floats_to_fixed(view.pts_to_pixels(self._points))]
            if len(self._points) > 1:
                cv2.polylines(img, coords, False, self._color, self._thickness, lineType=cv2.LINE_AA, shift=PREC_BITS)


class LineVec(PencilVec):
    """
    Line vector connects the first and last points.
    """
    _NAME = 'line'
    def add_point(self, xy, view=None):
        # only keep the first and last points:
        xy_board = view.pts_from_pixels(xy) if view is not None else xy

        super().add_point(xy_board)
        if len(self._points) > 2:
            self._points = [self._points[0], self._points[-1]]


class CircleVec(LineVec):
    """
    Circle vector is defined by the center and a point on the circumference, a LineVec rendered differently.
    """
    def __init__(self, color, thickness):
        super().__init__(color, thickness)
        self._last_view = None  # need to re-sample when this changes
        self._draw_pts = None

    def _calc(self, view):
        center =np.array(self._points[0])
        radius = np.linalg.norm(np.array(self._points[1]) - center)
        circle_pts = get_circle_points(center, radius)
        self._draw_pts = [floats_to_fixed(view.pts_to_pixels(circle_pts))]

    _NAME = 'circle'
    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            if self._last_view is None or view != self._last_view:
                self._calc(view)
                self._last_view = view
            cv2.polylines(img, self._draw_pts, True, self._color, self._thickness, lineType=cv2.LINE_AA, shift=PREC_BITS)


class RectangleVec(CircleVec):
    """
    Rectangle vector is defined by two opposite corners, also a LineVec subclass.
    """
    _NAME = 'rectangle'
    def _calc(self, view):
        x1, y1 = self._points[0]
        x2, y2 = self._points[1]
        x = [x1, x2, x2, x1, x1]
        y = [y1, y1, y2, y2, y1]
        rect_pts = np.array([x, y]).T
        self._draw_pts = [floats_to_fixed(view.pts_to_pixels(rect_pts))]