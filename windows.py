import json
from layout import BOARD_LAYOUT, COLORS_RGB, CONTROL_LAYOUT
import logging
import numpy as np
from enum import IntEnum
from gui_components import UIWindow, BoardView, MouseReturnStates, Window
from tools import Tool
import cv2
from util import in_bbox
from abc import ABC, abstractmethod
from controls import ControlBox, Toolbox, ColorBox
from slider import Slider


class ControlWindow(Window):
    """
    The control window where all the tools and controls are.
    It's drawing area is represented inside the control box in the board window.
    It is the zoomed-in view of the board window for high-precision drawing.
    """
    def __init__(self, name, size, bkg_color, view):
        super().__init__(name, size, bkg_color, view)

    def _init_controls(self):
        # Add toolbox, colorbox, zoom slider
        pass

    def mouse_event(self, event, x, y, flags, param):
        """
        Mouse event in the control window:
            - Check if it's captured by a current tool/control.
            - Check all control panels.
            - Send to current tool.
        """
        if self._element_with_mouse is not None:
            rv = self._element_with_mouse.mouse_event(event, x, y, self._ctrl_view)
            if rv == MouseReturnStates.released:
                self._element_with_mouse = None
        else:
            for control in self._controls:
                # Controls check if the mouse is in their bbox.
                rv = control.mouse_event(event, x, y, self._ctrl_view)
                if rv == MouseReturnStates.captured:
                    self._element_with_mouse = control
                    return
        current_tool = self._board.get_current_tool()
        rv = current_tool.mouse_event(event, x, y, self._ctrl_view)
        if rv == MouseReturnStates.captured:
            self._element_with_mouse = current_tool


class BoardWindow(Window):
    """
    The board window is the main window for viewing the board.
    It has toolbox for a pan tool, or can use whatever tool is selected in the control window.
    """

    def __init__(self, name, size, bkg_color, view):
        super().__init__(name, size, bkg_color, view)
        self._control_box = ControlBox(self._board, 'ControlBox', (0, 0), (0, 0), COLORS_RGB['black'])