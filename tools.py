from gui_components import UIElement
from abc import ABC, abstractmethod
import cv2
import numpy as np
from vectors import PencilVec, LineVec, RectVec, CircleVec


class Tool(UIElement):
    """
    things used to create different kinds of vector objects or manipulate them (pencil, line, ...)
    """

    def __init__(self, canvas):
        self._canvas = canvas
        self._active_vec = None  # in-progress vector object

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        Tool is being used, create/modify a vector object, or send it to the 
        canvas if it's finished.
        """
        pass

    def render(self, img):
        # TODO:  Render cursors here?
        if self._active_vec is not None:
            self._active_vec.render(img)

    def in_bbox(self, xy):
        return None


    def render(self, img):
        # override if vectors in progress require special rendering
        if self._active_vec is not None:
            self._active_vec.render(img)


class Pencil(Tool):
    # Freehand drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = PencilVec(self._canvas, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._canvas.add_vector(self._active_vec)
                self._active_vec = None


class Line(Tool):
    # Line drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = LineVec(self._canvas, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._canvas.add_vector(self._active_vec)
                self._active_vec = None


class Rectangle(Tool):
    # Rectangle drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = RectVec(self._canvas, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._canvas.add_vector(self._active_vec)
                self._active_vec = None


class Circle(Tool):
    # Circle drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = CircleVec(self._canvas, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._canvas.add_vector(self._active_vec)
                self._active_vec = None 


class Pan(Tool):
    # Pan tool (for canvas window)
    def __init__(self, canvas):
        super().__init__(canvas)
    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._canvas.start_pan(click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._m_down_pos is not None:
                self._canvas.pan(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            self._canvas.end_pan()
            self._m_down_pos = None


            

class Select(Tool):
    # Defined by bbox, vectors are selected 
    pass
    