import json
from layout import BOARD_LAYOUT, COLORS_BGR, CONTROL_LAYOUT
import logging
import numpy as np
from enum import IntEnum
from gui_components import UIWindow, BoardView, MouseReturnStates
from tools import Tool
import cv2
from util import in_bbox
from abc import ABC, abstractmethod

from controls import ControlManager
from vector_manager import VectorManager
from tools import ToolManager
from zoom_window import BoardBBox


def get_color_names():
    return [c for row in CONTROL_LAYOUT['control_box']['colors'] for c in row]


class Board(object):
    """
    A Board represents an unbounded drawing area and The board stores the list of vector drawing elements.

    The Board Window and Control Window each have views (bounding boxes) defined by their origin and zoom.
    The Control window has all the drawing/file toolboxes.
    THe Board has two controls:  zoom, and a box showing the outline of the current control window's view.
    Mouse signals to both windows draw with the current tool (unless using a control in either).

    Renders both windows.
    """

    def __init__(self, state_file):
        """
        :param vectors: list of Vector objects.
        """
        self.default_color_v = COLORS_BGR[BOARD_LAYOUT['default_color']]
        self.color_names = get_color_names()  # user selectable colors

        # Three kinds of UI elements, can talk to each other via the shared board object:
        self.vectors = VectorManager(self, state_file)
        self.controls = ControlManager(self)
        self.tools = ToolManager(self)

        # Windows will create controls that belong in them, and add them via add_element(), but
        # We need to create the Zoom*Control objects here because it will intercept mouse signals,
        # and have a presence in both windows, and they share state (the board bbox).
        bbb = BoardBBox(x_span=BOARD_LAYOUT['init_zoom_window_extent']['x'],
                        y_span=BOARD_LAYOUT['init_zoom_window_extent']['y'])
        self.controls.add_element(bbb.makeViewControl(self, self.controls))
        self.controls.add_element(bbb.makeViewControl(self, self.controls))

    def add_vector(self, vector):
        self._vectors.append(vector)

    def _init_tools(self):
        self._tools = []

        # special tool for board window, grabing in the box moves the control window,
        # grabing outside pans the board:
        self._controls = []

    def _init_controls(self):
        self._ui_elements = []  # list of UIElement objects on the board, UI buttons, tools, etc.

    def get_frames(self):
        """
        Return the current frames for the board and control windows.
        """
        canv_frame = self._get_canv_frame()
        ctrl_frame = self._get_ctrl_frame()
        return canv_frame, ctrl_frame

    def _get_canv_frame(self):
        if self._frame is None:
            self._frame = np.zeros((self._window_size[1], self._window_size[0], 3), np.uint8)

            self._frame[:] = self.bkg_color_v
            for vector in self.vectors:
                vector.render(self._frame)
            for element in self._elements:
                element.render(self._frame)

        return self._frame

    def canv_mouse_callback(self, event, x, y, flags, param):
        """

        """

    def _mouse_callback(self, event, x, y, view):
        """
        On a mouse event, if the mouse is in use, send the event the relevent element.
        Otherwise, send to the current tool.
        :param view: a BoardView object.
        """
        pos = np.array([x, y])

        if event == cv2.EVENT_LBUTTONDOWN:
            # if self._element_with_mouse is not None:
            #    logging.warning("Mouse down while element active.")
            #    self._element_with_mouse = None

            for i, element in enumerate(self._elements):
                if element.in_bbox(pos):
                    self._element_with_mouse = element
                    element.mouse_event(event, pos)
                    break

        elif

    def keypress(self, key):
        if self._element_with_mouse is not None:
            self._element_with_mouse.keypress(key)
        else:
            self._current_tool.keypress(key)
