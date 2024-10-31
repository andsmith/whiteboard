import json
from layout import BOARD_LAYOUT, COLORS_BGR, CONTROL_LAYOUT
import logging
import numpy as np
from enum import IntEnum
from gui_components import MouseReturnStates
from tools import Tool
import cv2
from util import unit_to_abs_bbox
from abc import ABC, abstractmethod
# from controls import ControlBox, Toolbox, ColorBox
from board_view import BoardView
from slider import Slider
from button_box import ButtonBox
from buttons import Button, ColorButton, ToolButton
from layout import COLORS_BGR, CONTROL_LAYOUT, EMPTY_BBOX


class UIWindow(ABC):
    """
    Base class for windows that have a view of the board.
    Windows get managers from the board, keep track of which has captured the mouse, where to send signals, etc.
    """

    def __init__(self, name, board_view, vector_manager, tool_manager, title, window_size, visible=True,
                 win_params=cv2.WINDOW_NORMAL, bkg_color_n='off_white'):
        self._name = name  # (for cv2)
        self._window_size = window_size
        self._win_params = win_params
        self._title = title
        self._visible = visible

        # for rendering window:
        self._color_v = COLORS_BGR[bkg_color_n]
        self._blank = (np.zeros((window_size[1], window_size[0], 3)) + self._color_v).astype(dtype=np.uint8)
        self._pan_start_xy = None

        # for tracking & dispatching mouse signals:
        self._control_with_mouse = None  # index
        self._tool_has_mouse = False
        self._cur_xy = None
        self._click_xy = None
        self._control_moused_over = None

        # controls, state & managers:
        self._view = board_view
        self.vectors = vector_manager
        self.tools = tool_manager
        self._controls = []

    def add_control(self, control):
        self._controls.append(control)

    def start(self):
        cv2.namedWindow(self._name, self._title)
        cv2.resizeWindow(self._name, self._window_size[0], self._window_size[1])
        cv2.setMouseCallback(self._name, self.cv2_mouse_event, param=self._name)

    def refresh(self):
        frame = self._blank.copy()
        self.vectors.render(frame, self._view)
        for control in self._controls:
            control.render(frame, self._view)
        cv2.imshow(self._title, frame)

    def _update_mouseover(self, xy):
        for i, control in enumerate(self._controls):
            if control.in_bbox(xy):
                control.mouseover(xy, self._view)
                self._control_moused_over = i
                return
        if self._control_moused_over is not None:
            self._controls[self._control_moused_over].mouseout(self._view)
            self._control_moused_over = None

    def cv2_mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            self._update_mouseover((x, y))
            self._cur_xy = (x, y)
            
        if self._tool_has_mouse:
            rv = self.tools.mouse_event(event, (x, y), self._view)
            if rv == MouseReturnStates.released:
                self._tool_has_mouse = False
            elif rv == MouseReturnStates.unused:
                raise Exception("Tool didn't use the mouse signal after capturing it.")
            return

        if self._control_with_mouse is not None:
            rv = self._controls[self._control_with_mouse].mouse_event(event, (x, y), self._view)
            if rv == MouseReturnStates.released:
                self._control_with_mouse = None
            elif rv == MouseReturnStates.unused:
                raise Exception("Control didn't use the mouse signal after capturing it.")
            return  # don't keep processing

        # if not, check all controls bboxes and send to the first that uses it.
        for i, control in enumerate(self._controls):
            if control.in_bbox((x, y)):
                rv = control.mouse_event(event, (x, y), self._view)
                if rv == MouseReturnStates.captured:
                    self._control_with_mouse = i
                    return
        # if no control used it, send to the tool.
        rv = self.tools.mouse_event(event, (x, y), self._view)
        if rv == MouseReturnStates.captured:
            self._tool_has_mouse = True

    def close(self):
        cv2.destroyWindow(self._name)
        