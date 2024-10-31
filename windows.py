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
        self._name = name  # i.e. 'control' or 'board'
        self._visible = visible
        self._color_v = COLORS_BGR[bkg_color_n]
        self._blank = (np.zeros((window_size[1], window_size[0], 3)) + self._color_v).astype(dtype=np.uint8)
        self._window_size = window_size
        self._win_params = win_params
        self._title = title
        self._managers = self._make_managers()
        self._captured_ind = None  # index of self._managers
        self._view = board_view
        self.vectors = vector_manager
        self.tools = tool_manager


    @abstractmethod
    def _make_managers(self):
        """
        Create the control and tool managers for this window.
        """
        pass

    def get_win_name(self):
        return self._name  # so cv2 knows which

    @abstractmethod
    def _get_init_board_view(self):
        """
        What portion of the board is visible in this window.
        :return: BoardView object
        """
        pass

    def _init_win(self):

        cv2.namedWindow(self._name, self._title)
        cv2.resizeWindow(self._name, self._bbox['x'][1], self._bbox['y'][1])
        cv2.setMouseCallback(self.name, self.cv2_mouse_event, param=self.name)

    def refresh(self):
        frame = self._blank.copy()
        self.render(frame)
        cv2.imshow(self._title, self._frame)

    def cv2_mouse_event(self, event, x, y, flags, param):

        # see if any manager has it captured:
        if self._captured is not None:
            rv = self._managers[self._captured].mouse_event(event, (x, y), param)
            if rv == MouseReturnStates.released:
                self._captured = None
            elif rv == MouseReturnStates.unused:
                raise Exception("Manager %s didn't use the mouse signal after capturing it." % self._captured)
            return rv

        # If not send to all managers and let the first one that wants it capture it:
        for manager in self._MOUSE_SIGNAL_ORDER:
            rv = self._managers[manager].mouse_event(event, (x, y), param)
            if rv == MouseReturnStates.captured:
                self._captured = manager
                return rv
            elif rv == MouseReturnStates.released:
                raise Exception("Manager %s released the mouse without capturing it." % manager)

        return MouseReturnStates.unused

    def render(self, img):
        self._vector_m.render(img)
        self._managers['controls'].render(img)
        self._managers['tools'].render(img)


class ControlWindow(UIWindow):
    """
    The control window where all the tools and controls are. (Instantiate one.)
    It's drawing area is represented inside the control box in the board window.
    It is the zoomed-in view of the board window for high-precision drawing.
    """

    def __init__(self, board):
        size = CONTROL_LAYOUT['win_size']
        bkg_color = CONTROL_LAYOUT['bkg_color']
        win_name = CONTROL_LAYOUT['win_name']
        win_size = CONTROL_LAYOUT['win_size']
        super().__init__(board, 'control', size, bkg_color, win_name, win_size)

        self._init_controls()

    def _init_controls(self):
        # Color buttons
        color_name_grid = CONTROL_LAYOUT['color_box']['options']
        color_buttons = [[ColorButton(self._board, "CB: %s" % (color_name,), EMPTY_BBOX, color_name)
                          for color_name in row]
                         for row in color_name_grid]
        color_button_bbox = unit_to_abs_bbox(CONTROL_LAYOUT['color_box']['loc'], self._window_size)
        color_control = ButtonBox(self._board, 'color_button_box', color_button_bbox, color_buttons, exclusive=True)

        # Tool buttons
        tool_name_grid = CONTROL_LAYOUT['tool_box']['options']
        tool_buttons = [[ToolButton(self._board, "TB: %s" % (tool_name,), EMPTY_BBOX, tool_name)
                         for tool_name in row]
                        for row in tool_name_grid]
        tool_button_box = unit_to_abs_bbox(CONTROL_LAYOUT['tool_box']['loc'], self._window_size)
        tool_control = ButtonBox(self._board, 'tool_button_box', tool_button_box, tool_buttons, exclusive=True)

        # zoom slider
        zoom_slider_box = unit_to_abs_bbox(CONTROL_LAYOUT['zoom_slider']['loc'], self._window_size)
        zoom_slider = Slider(self._board, zoom_slider_box, 'control_zoom_slider',
                             orientation=CONTROL_LAYOUT['zoom_slider']['orientation'],
                             values=[-10, 10], init_pos=0.5)

        # now add them to the control manager:
        self._managers['controls'].add_element(color_control)
        self._managers['controls'].add_element(tool_control)
        self._managers['controls'].add_element(zoom_slider)

        # But not the ZoomWindow, since it needs mouse signals to be intercepted first.

    def mouse_event(self, event, x, y, flags, param):
        pass

    def _get_init_board_view(self):
        """
        Initial mapping of the board to the control window is entirely determined by the initial
        mapping of the board to the board window and the initial position of the ZoomWindow.
        """
        return BoardView(self._name, self._window_size, (0, 0), 1)


class BoardWindow(UIWindow):
    """
    The board window is the main window for viewing the board.
    It has toolbox for a pan tool, or can use whatever tool is selected in the control window.
    """

    def __init__(self, name, size, bkg_color, view):
        super().__init__(name, size, bkg_color, view)
        self._control_box = ControlBox(self._board, 'ControlBox', (0, 0), (0, 0), COLORS_RGB['black'])

    def _get_init_board_view(self):
        # determine from window size and layout
        bc = BoardView(self._name, self._window_size, (0, 0), 1)

    def mouse_event(self, event, x, y, flags, param):
        pass
