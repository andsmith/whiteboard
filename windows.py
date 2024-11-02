import json
from layout import BOARD_LAYOUT, COLORS_BGR, CONTROL_LAYOUT
import logging
import numpy as np
from enum import IntEnum
from gui_components import MouseReturnStates
from tools import Tool
import cv2
from board_view import BoardView
from slider import Slider
from button_box import ButtonBox
from buttons import Button, ColorButton, ToolButton
from layout import COLORS_BGR, CONTROL_LAYOUT, EMPTY_BBOX


class UIWindow(object):
    """
    All windows should instantiate this class.
    Windows get managers from the board, keep track of which has captured the mouse, where to send mouse/keyboard signals, etc.
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
        self._draw_color_v = COLORS_BGR[BOARD_LAYOUT['obj_color']]
        self._blank = (np.zeros((window_size[1], window_size[0], 3)) + self._color_v).astype(dtype=np.uint8)
        self._pan_start_xy = None
        self._old_view = None

        # for tracking & dispatching mouse signals:
        self._control_with_mouse = None  # index
        self._tool_has_mouse = False
        self._cur_xy = None
        self._click_xy = None
        self._control_moused_over = None

        # controls, state & managers:
        self.view = board_view
        self.vectors = vector_manager
        self.tools = tool_manager
        self._controls = []

    def get_name_and_title(self):
        return self._name, self._title

    def start_pan(self, xy):
        self._pan_start_xy = np.array(xy)
        self._old_view = self.view

    def end_pan(self):
        self._pan_start_xy = None
        self._old_view = None

    def pan_to(self, xy):
        rel_xy = np.array(xy) - self._pan_start_xy
        self.view = self._old_view.get_panned_view(rel_xy)

    def set_zoom(self, zoom):
        self.view = self.view.get_zoomed_view(zoom)

    def add_control(self, control):
        self._controls.append(control)

    def start(self):
        cv2.namedWindow(self._title)
        cv2.resizeWindow(self._title, self._window_size[0], self._window_size[1])
        cv2.setMouseCallback(self._title, self.cv2_mouse_event, param=self._name)

    def refresh(self, options = {}):
        frame = self._blank.copy()
        if 'show_grid' in options and options['show_grid']:
            self.view.render_grid(frame, line_color_v = self._draw_color_v, bkg_color_v = self._color_v)
        self.vectors.render(frame, self.view)
        for control in self._controls:
            control.render(frame)
        cv2.imshow(self._title, frame)

    def _update_mouseover(self, xy):
        for i, control in enumerate(self._controls):
            if control.in_bbox(xy):
                control.mouse_over(xy)
                self._control_moused_over = i
                return
        if self._control_moused_over is not None:
            self._controls[self._control_moused_over].mouse_out(xy)
            self._control_moused_over = None

    def cv2_mouse_event(self, event, x, y, flags, param):
        """
        Figure out which tool/control has the mouse (if any), or which should get it, 
        then call the appropriate mouse_<event> method
        """
        if event == cv2.EVENT_MOUSEMOVE:
            self._update_mouseover((x, y))
            self._cur_xy = (x, y)

            if self._control_with_mouse is not None:
                rv = self._controls[self._control_with_mouse].mouse_move((x, y))
                if rv == MouseReturnStates.released:
                    self._control_with_mouse = None
                    
            if self._tool_has_mouse:
                rv = self.tools.current_tool.mouse_move((x, y),self)
                if rv == MouseReturnStates.released:
                    self._tool_has_mouse = False
                    
                
        elif event == cv2.EVENT_LBUTTONDOWN:
            if self._control_with_mouse is not None or self._tool_has_mouse:
                raise Exception("control already has mouse")
            for i, control in enumerate(self._controls):
                if control.in_bbox((x, y)):
                    rv = control.mouse_down((x, y))
                    if rv == MouseReturnStates.captured:
                        self._control_with_mouse = i
                    if rv in [MouseReturnStates.captured, MouseReturnStates.released]:
                        return

            rv = self.tools.current_tool.mouse_down((x, y),self)
            if rv == MouseReturnStates.captured:
                self._tool_has_mouse = True
            
        elif event == cv2.EVENT_LBUTTONUP:
            if self._control_with_mouse is not None:
                rv = self._controls[self._control_with_mouse].mouse_up((x, y))
                if rv == MouseReturnStates.released:
                    self._control_with_mouse = None
                
            elif self._tool_has_mouse:
                rv = self.tools.current_tool.mouse_up((x, y),self)
                if rv == MouseReturnStates.released:
                    self._tool_has_mouse = False
                return
    def keypress(self, key):
        if key & 0xff != 255:
            print("Window %s pressed key %s." % (self._title, key))
        return True
                    
            
    def close(self):
        cv2.destroyWindow(self._title)
        