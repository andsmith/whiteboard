"""
Class to represent simple vector drawing shapes.
"""
from gui_components import Renderable
import cv2

import numpy as np
from layout import COLORS_BGR, VECTOR_DEF, EMPTY_BBOX, TEXT_TOOL
from abc import ABC, abstractmethod
from util import get_bbox, PREC_BITS, PREC_SCALE, floats_to_fixed, get_circle_points
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
        self.highlighted = False
        self._points = []

        super().__init__(self.__class__.__name__, EMPTY_BBOX)

    def __eq__(self, other):
        # compare timestamps?
        equal = self._color == other._color and \
            self._thickness == other._thickness and \
            np.isclose(self._points, other._points).all()
        return equal

    def copy(self):
        c = self.__class__(self._color, self._thickness)
        c._points = self._points.copy()
        c._bbox = self._bbox.copy()
        c._finalized_t = time.perf_counter()  # ???
        return c

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
        self._centroid = np.mean(self._points, axis=0)

    def get_centroid(self):
        return self._centroid

    def move_to(self, xy):
        """
        Move the vector (centroid) to the given point.
        :param xy: (x, y) point in board coordinates.
        """
        xy = np.array(xy)
        self._points += xy - self._centroid
        self._centroid = xy
        self._bbox = get_bbox(self._points)

    def add_point(self, xy, view=None):
        """
        User moved the mouse, add the new point.
        :param xy: the point to add, assumed to be pixel coords (ints) if view is not None, else board coords (floats).
        :param view: BoardView object
        """
        xy_board = view.pts_from_pixels(xy) if view is not None else xy
        print(self.name, "add_point", xy_board)

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

    def _get_color(self, color_v):
        if self.highlighted:
            return COLORS_BGR['neon green']
        return color_v


class PencilVec(Vector):
    """
    Pencil stroke connects the sequence of points a line that has the given properties.
    """
    _NAME = 'pencil'

    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            coords = [floats_to_fixed(view.pts_to_pixels(self._points))]
            if len(self._points) > 1:
                color = self._get_color(self._color)
                cv2.polylines(img, coords, False, color, self._thickness, lineType=cv2.LINE_AA, shift=PREC_BITS)


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
        self._view_cache = {}  # {view.win_name: (view, draw_pts), ...}

    def add_point(self, xy, view=None):
        # invalidate cache for all views

        self._view_cache = {}

        rv = super().add_point(xy, view)
        return rv

    def _recalc_pts(self, view):
        center = np.array(self._points[0])
        radius = np.linalg.norm(np.array(self._points[1]) - center)
        circle_pts = get_circle_points(center, radius)
        draw_pts = floats_to_fixed(view.pts_to_pixels(circle_pts))
        return [draw_pts]

    def _get_draw_points(self, view):
        """
        Don't want to recalculate the circle points (on-screen pixel locations) every frame, 
        only when the view changes.
        """
        if len(self._points) < 2:
            return

        old_view, draw_pts = self._view_cache.get(view.win_name, (None, None))
        if old_view is None or view != old_view or draw_pts is None:
            draw_pts = self._recalc_pts(view)
            self._view_cache[view.win_name] = view, draw_pts
        return draw_pts

    _NAME = 'circle'

    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            draw_pts = self._get_draw_points(view)
            if draw_pts is not None:
                color = self._get_color(self._color)
                cv2.polylines(img, draw_pts, True, color,
                              self._thickness, lineType=cv2.LINE_AA, shift=PREC_BITS)


class RectangleVec(CircleVec):
    """
    Rectangle vector is defined by two opposite corners, also a LineVec subclass.
    """
    _NAME = 'rectangle'

    def _recalc_pts(self, view):
        x1, y1 = self._points[0]
        x2, y2 = self._points[1]
        x = [x1, x2, x2, x1, x1]
        y = [y1, y1, y2, y2, y1]
        rect_pts = np.array([x, y]).T
        return [floats_to_fixed(view.pts_to_pixels(rect_pts))]


class TextVec(Vector):
    """
    Text vector is defined by a point, a string, and a size.
    """
    _NAME = 'text'

    def __init__(self, color, text_size):
        super().__init__(color, thickness=0)
        self._text = ""
        self._text_size = text_size
        self._font = TEXT_TOOL['font']

    @staticmethod
    def scale_and_thickness_from_size( size):
        t_scale = size/40
        t_thickness = 1
        if t_scale > .4:
            t_thickness = 2
        return t_scale, t_thickness
    
    def add_point(self, xy, view=None):
        print(self.name, "add_point", xy)
        if view is not None:
            xy = view.pts_from_pixels(xy)
        self._points = [xy]

    def add_letters(self, letters):
        self._text += letters

    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            xy = (np.array(view.pts_to_pixels(self._points[0]),dtype=np.int32))  # no high-precision available for cv2.putText
            color = self._get_color(self._color)
            t_scale, t_thickness = TextVec.scale_and_thickness_from_size(self._text_size)
            zoom =view.get_scope()[0]
            t_scale *= zoom
            cv2.putText(img, self._text, xy, self._font, float(t_scale), color, t_thickness, cv2.LINE_AA)

    def get_data(self):
        data = super().get_data()
        data['text'] = self._text
        data['text_size'] = self._text_size
        return data

    @classmethod
    def from_data(cls, data):
        r = cls(data['color'], data['thickness'], data['text'], data['text_size'])
        r._points = data['points']
        r._bbox = get_bbox(r._points)
        r._finalized_t = data['timestamp']
        return r
