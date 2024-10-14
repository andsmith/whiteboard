"""
Class to represent simple vector drawing shapes.
"""
from gui_components import UIElement, UIManager, BoardView
import cv2
import numpy as np
from layout import COLORS_RGB, VECTORS, EMPTY_BBOX
from abc import ABC, abstractmethod, abstractstaticmethod
from util import get_bbox, bboxes_intersect
import json
import time


class Vector(UIElement, ABC):
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
        :param color: (r, g, b) tuple
        :param thickness: int
        """
        self._highlight_level = 0  # 0 = no highlight, 1 = selected  (TODO: 2 = hovered, 3 = ?, ...)
        self._finalized_t = None  # time when the vector was finalized, in epoch.
        self._color = color
        self._thickness = thickness
        self._points = []

        super().__init__('Vector', EMPTY_BBOX, visible=True, pinned=True)

    @abstractmethod
    def get_data(self):
        """
        Return the data needed to serialize this vector (must be JSON-able).
        """
        pass

    @abstractmethod
    @staticmethod
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

    def add_point(self, xy_board):
        self._points.append(xy_board)
        self._bbox = get_bbox(self._points)

    def get_data(self):
        if self._finalized_t is None:
            raise ValueError("Vector not finalized, don't serialize!")

        data = {'color': self._color,
                'thickness': self._thickness,
                'points': self._points,
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

    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            thickness = int(self._thickness * view.zoom)
            thickness += self._highlight_level * 2  # add 2 pixels per highlight (regardless of zoom)
            coords = view.to_pixels(self._points)
            if len(self._points) > 1:
                cv2.polylines(img, [np.array(coords)], False, self._color, self._thickness, lineType=cv2.LINE_AA)


class LineVec(PencilVec):
    """
    Line vector connects the first and last points.
    """

    def add_point(self, xy_board):
        super().add_point(xy_board)
        if len(self._points) > 2:
            self._points = [self._points[0], self._points[-1]]


class CircleVec(LineVec):
    """
    Circle vector is defined by the center and a point on the circumference.
    """

    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            thickness = int(self._thickness * view.zoom)
            thickness += self._highlight_level * 2  # add 2 pixels per highlight (regardless of zoom)
            coords = self._points_to_px(view)
            center, radius = coords[0], np.linalg.norm(coords[1] - coords[0])
            cv2.circle(img, tuple(center), int(radius), self._color, thickness, lineType=cv2.LINE_AA)


class RectangleVec(LineVec):
    """
    Rectangle vector is defined by two opposite corners.
    """

    def render(self, img, view):
        if view.sees_bbox(self._bbox):
            thickness = int(self._thickness * view.zoom)
            thickness += self._highlight_level * 2  # add 2 pixels per highlight (regardless of zoom)
            coords = self._points_to_px(view)
            cv2.rectangle(img, tuple(coords[0]), tuple(coords[1]), self._color, thickness, lineType=cv2.LINE_AA)
