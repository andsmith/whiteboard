from gui_components import  MouseReturnStates
from abc import ABC, abstractmethod
import cv2
import numpy as np
from vectors import PencilVec, LineVec, RectangleVec, CircleVec
from layout import COLORS_RGB, CONTROL_LAYOUT
import logging

class Tool(ABC):
    """
    things used to create different kinds of vector objects or manipulate them (pencil, line, ...)
    """

    def __init__(self, tool_manager):
        self._manger = tool_manager
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


class Pencil(Tool):
    # Freehand drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = PencilVec(*self._manger.get_color_thickness())
            self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._manager.commit_vector(self._active_vec)
                self._active_vec = None


class Line(Tool):
    # Line drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = LineVec(*self._manger.get_color_thickness())
            self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._manager.commit_vector(self._active_vec)
                self._active_vec = None


class Rectangle(Tool):
    # Rectangle drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = RectangleVec(*self._manger.get_color_thickness())
            self._active_vec.add_point(click_pos)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._manager.commit_vector(self._active_vec)
                self._active_vec = None


class Circle(Tool):
    # Circle drawing tool.

    def mouse_event(self, event, x, y, flags, param):
        click_pos = np.array([x, y])
        if event == cv2.EVENT_LBUTTONDOWN:
            self._active_vec = CircleVec(*self._manger.get_color_thickness())
            self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._active_vec is not None:
                self._active_vec.add_point(click_pos)
        elif event == cv2.EVENT_LBUTTONUP:
            if self._active_vec is not None:
                self._active_vec.finalize()
                self._manager.commit_vector(self._active_vec)
                self._active_vec = None 

"""
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
    
"""
class ToolManager(object):
    # Manages anything user uses to change the whiteboard.
    _TOOLS = {'pencil': Pencil,
              'line': Line,
              'rectangle': Rectangle,
              'circle': Circle,}
              #'pan': Pan,
              #'select': Select

    def __init__(self, vector_manager, init_tool_name = 'pencil', init_color = 'black', init_thickness = 2):
        self._vectors = vector_manager
        self._color_n = init_color
        self._thickness = init_thickness 
        self._current_tool_ind = None
        self._init_tools()
        self.switch_tool(init_tool_name)

        self.tool = 

    def commit_vector(self, vector):
        self._vectors.add_vector(vector)
        
    def switch_tool(self, new_tool_name):
        try:
            self._current_tool_ind = self._tools.index(self._tools[new_tool_name])
        except KeyError:
            raise ValueError(f'Invalid tool name (did you add to self._tools in _init_elements?): {new_tool_name}')
        logging.info(f"Switched to tool: {new_tool_name}")
        
    def _init_tools(self):
        self._tools = {'pencil': Pencil(self),
                       'line': Line(self),
                       'rectangle': Rectangle(self),
                       'circle': Circle(self),}
                       #'pan': Pan(self),
                       #'select': Select(self)
        
        self._tool_list = list(self._tools.values())

    def set_color_thickness(self, color_name=None, thickness=None):
        self._color_n = color_name if color_name is not None else self._color_n
        self._thickness = thickness if thickness is not None else self._thickness

    def get_color_thickness(self):
        return self._color_n, self._thickness

    def render(self, img):
        pass

    def mouse_event(self, event, x, y, flags, param):
        """
        Send the mouse event to the current tool.
        """
        return self._tool_list[self._current_tool_ind].mouse_event(event, x, y, flags, param)