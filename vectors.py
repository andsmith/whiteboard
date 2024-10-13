"""
Class to represent simple vector drawing shapes.
"""
from gui_components import BoardView
import cv2
import numpy as np
from layout import COLORS_RGB, VECTORS
from abc import ABC, abstractmethod
from util import in_bbox



class VectorManager(object):
    """
    Manages set of vectors on the board.
    """




class Vector(ABC):
    """
    Represents some change to the canvas, e.g., line, circle, pencil stroke.
    Store all coordinates & properties.

    When objects are first created, or when selected, they are 'unfinalized' (i.e. in progress).
    Unfinalized objects may be drawn differently.
    Objects are finalized when the user releases the mouse button (etc.).

    The canvas is rendered by applying the list of vectors to a blank image.


    Undoing is removing the last vector, pushing it to the redo stack, etc.
    """

    def __init__(self, canvas, init_point_px):
        """
        :param canvas: Board object
        :param init_point_px: (x, y) tuple, initial point in pixels.
        """
        self._canvas = canvas
        self._color = canvas.current_color
        self._points = []  # list of (x, y) tuples in canvas coordinates
        self.add_point(init_point_px)
        self._finalized = False

    def add_point(self, point_px):
        


    @abstractmethod
    def serialize(self):
        pass

    @abstractmethod
    def deserialize(self):
        pass

    @abstractmethod
    def render(self, img, origin, zoom, selected=False):
        """
        Draw the vector on the image, or whatever part is in bounds.
        :param img: np.array, image to draw on.
        :param origin: np.array, (x, y) of the top-left corner of the canvas.
        :param zoom: float, zoom factor. (higher means bigger)
        """
        pass

    @abstractmethod
    def point_dist(self, pt):
        """
        Return the distance to the vector object.
        """
        pass

    @abstractmethod
    def inside(bbox):
        """
        Returns True if any part of the vector will be visible in the bbox.
        """
        pass

    def finalize(self):
        self._finalized = True


class Line(Vector):
    def __init__(self, canvas, color, thickness, start, end):
        """
        :param canvas: Board object
        :param color: (r, g, b) tuple
        :param thickness: int
        :param start: (x, y) tuple
        :param end: (x, y) tuple
        """
        super().__init__(canvas)
        self._color = color
        self._thickness = thickness
        self._start = np.array(start)
        self._end = np.array(end)
        self._finalized = True

    def render(self, img):
        cv2.line(img, tuple(self._start), tuple(self._end), self._color, self._thickness)

    def inside(bbox):
        return 


    def serialize(self):
        return {'type': 'Line', 'color': self._color, 'thickness': self._thickness, 'start': self._start.tolist(), 'end': self._end.tolist()}

    @classmethod
    def deserialize(cls, canvas, data):
        return cls(canvas, data['color'], data['thickness'], data['start'], data['end'])