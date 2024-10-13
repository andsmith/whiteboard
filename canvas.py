import json
from layout import CANVAS_LAYOUT, COLORS_RGB, CONTROL_LAYOUT
import logging
import numpy as np
from enum import IntEnum
from gui_components import UIWindow, BoardView, MouseReturnStates
from tools import Tool
import cv2
from util import in_bbox
from abc import ABC, abstractmethod


class Board(object):
    """
    A Board represents an unbounded drawing area and The canvas stores the list of vector drawing elements.

    The Board Window and Control Window each have views (bounding boxes) defined by their origin and zoom.
    The Control window has all the drawing/file toolboxes.
    THe Board has two controls:  zoom, and a box showing the outline of the current control window's view.
    Mouse signals to both windows draw with the current tool (unless using a control in either).

    Renders both windows.
    """
    _CANVAS_MODES = ['pan', 'zoom']

    _WINDOWS = ['canvas', 'control']

    def __init__(self, canv_size, ctrl_size):
        """
        :param vectors: list of Vector objects.
        """
        self._canv_win_size = canv_size
        self._ctrl_win_size = ctrl_size
        logging.info("Board_window created: %i x %i." % canv_size)
        logging.info("Control_window created: %i x %i." % ctrl_size)
        self._canv_bkg_color = CANVAS_LAYOUT['bkg_color']
        self._ctrl_bkg_color = CONTROL_LAYOUT['bkg_color']
        self._blank_frames = {'canvas': np.zeros((self._canv_win_size[1],
                                                  self._canv_win_size[0], 3),
                                                 np.uint8) + self._canv_bkg_color,
                              'control': np.zeros((self._ctrl_win_size[1],
                                                   self._ctrl_win_size[0], 3),
                                                  np.uint8) + self._ctrl_bkg_color}
        # current frames for each window, set to None to force redraw.
        self._frames = {'canvas': None, 'control': None}

        # list of Vector objects already drawn (tools their Vector in progress).
        self._vectors = []

        # list of deleted Vector objects, self._deleted[0] is the most recently deleted Vector.
        self._deleted = []

        # UIElement object with mouse focus (either a control or a tool)
        self._element_w_mouse = None

        # canvas view changes as user pans/zooms, ctrl view changes as user moves control box
        self._views = {'canvas':BoardView(np.array(CANVAS_LAYOUT['origin']), CANVAS_LAYOUT['zoom']),
                        'control':BoardView(np.array(CONTROL_LAYOUT['origin']), CONTROL_LAYOUT['zoom'])}

        self._init_controls()
        self._init_tools()

        self._colors = CONTROL_LAYOUT['color_box']['options']
        self.current_color = self._colors[0]
        self._canvas_mode = self._CANVAS_MODES.pan

        # init

    def add_vector(self, vector):
        self._vectors.append(vector)

    def _init_tools(self):
        self._tools = []

        # special tool for canvas window, grabing in the box moves the control window,
        # grabing outside pans the canvas:
        self._controls = []

    def _init_controls(self):
        self._ui_elements = []  # list of UIElement objects on the canvas, UI buttons, tools, etc.

    def get_frames(self):
        """
        Return the current frames for the canvas and control windows.
        """
        canv_frame = self._get_canv_frame()
        ctrl_frame = self._get_ctrl_frame()
        return canv_frame, ctrl_frame

    def _get_canv_frame(self):
        if self._frame is None:
            self._frame = np.zeros((self._window_size[1], self._window_size[0], 3), np.uint8)

            self._frame[:] = self.bkg_color
            for vector in self.vectors:
                vector.render(self._frame)
            for element in self._elements:
                element.render(self._frame)

        return self._frame

    def save(self, filename):
        vectors = [vector.serialize() for vector in self.vectors]
        deleted = [vector.serialize() for vector in self._deleted]
        with open(filename, 'w') as f:
            json.dump([vectors, deleted], f)

    def load(self, filename):
        with open(filename, 'r') as f:
            load_data = json.load(f)
        self._vectors = [vector.deserialize() for vector in load_data[0]]
        self._deleted = [vector.deserialize() for vector in load_data[1]]

    def get_vector_at(self, xy):
        """
        Select the closest vector at the given coordinates.
        """
        # TODO:  store in B-tree for faster selection.
        dists = [vector.point_dist(xy) for vector in self.vectors]
        if min(dists) < self._max_click_dist:
            return self.vectors[np.argmin(dists)]
        return None

    def delete(self, vector):
        self._deleted.append(vector)
        self._vectors.remove(vector)

    def undo_delete(self):
        if self._deleted:
            self._vectors.append(self._deleted.pop())

        
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
