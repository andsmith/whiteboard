from gui_components import UIElement, UIManager, MouseReturnStates
from abc import ABC, abstractmethod
import cv2
import numpy as np
from vectors import PencilVec, LineVec, RectVec, CircleVec
from layout import COLORS_RGB, CONTROL_LAYOUT
import logging

class Tool(UIElement):
    """
    things used to create different kinds of vector objects or manipulate them (pencil, line, ...)
    """

    def __init__(self, board):
        self._board = board
        self._active_vec = None  # in-progress vector object

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        Tool is being used, create/modify a vector object, or send it to the 
        board if it's finished.
        """
        pass

    def render(self, img):
        # TODO:  Render cursors here?
        if self._active_vec is not None:
            self._active_vec.render(img)

    def in_bbox(self, xy):
        return None


    def render(self, img):
        # Override if vectors in progress require special rendering
        # or to render the tool itself as a cursor, etc.
        if self._active_vec is not None:
            self._active_vec.render(img)


class Pencil(Tool):
    # Freehand drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = PencilVec(self._board, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._board.add_vector(self._active_vec)
                self._active_vec = None


class Line(Tool):
    # Line drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = LineVec(self._board, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._board.add_vector(self._active_vec)
                self._active_vec = None


class Rectangle(Tool):
    # Rectangle drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = RectVec(self._board, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._board.add_vector(self._active_vec)
                self._active_vec = None


class Circle(Tool):
    # Circle drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = CircleVec(self._board, click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._board.add_vector(self._active_vec)
                self._active_vec = None 


class Pan(Tool):
    # Pan tool (for board window)
    def __init__(self, board):
        super().__init__(board)
    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._board.start_pan(click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._m_down_pos is not None:
                self._board.pan(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            self._board.end_pan()
            self._m_down_pos = None


            

class Select(Tool):
    # Defined by bbox, vectors are selected 
    pass
    

class ToolManager(UIManager):
    # Manages anything user uses to change the board.
    _TOOLS = {'pencil': Pencil,
              'line': Line,
              'rectangle': Rectangle,
              'circle': Circle,
              'pan': Pan,
              'select': Select}

    def __init__(self, board, init_tool_name = 'pencil', init_color = 'black', init_thickness = 2):
        super().__init__(board, 'Tool Manager', None, visible=False)
        self._color = init_color
        self._thickness = init_thickness 
        self.switch_tool(init_tool_name)
        
    def switch_tool(self, new_tool_name):
        try:
            self._current_tool_ind = self._tools.index(self._tools[new_tool_name])
        except KeyError:
            raise ValueError(f'Invalid tool name (did you add to self._tools in _init_elements?): {new_tool_name}')
        logging.info(f"Switched to tool: {new_tool_name}")
        
    def _init_elements(self):
        self._tools = {'pencil': Pencil(self._board),
                       'line': Line(self._board),
                       'rectangle': Rectangle(self._board),
                       'circle': Circle(self._board),
                       'pan': Pan(self._board),
                       'select': Select(self._board)}
        
        self._tool_list = list(self._tools.values())

    def set_color(self, color_name):
        self._color = color_name

    def render(self, img):
        pass

    def mouse_event(self, event, x, y, flags, param):
        """
        Send the mouse event to the current tool.
        """
        return self._tool_list[self._current_tool_ind].mouse_event(event, x, y, flags, param)