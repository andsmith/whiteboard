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
    def mouse_down(self, xy, window):
        """
        Starting to use the tool.
        :param xy: (x, y) position of mouse in pixels
        :param window: UIWindow object mouse clicked in.
        """
        pass

    @abstractmethod
    def mouse_move(self, xy, window):
        pass

    @abstractmethod
    def mouse_up(self, xy, window):
        pass
    
    def render(self, img):
        # TODO:  Render cursors here?
        if self._active_vec is not None:
            self._active_vec.render(img)


class Pencil(Tool):
    def mouse_down(self, xy, window):
        self._active_vec = PencilVec(*self._manger.get_color_thickness())
        self._active_vec.add_point(xy, window.view)

    def mouse_move(self, xy,window):
        if self._active_vec is not None:
            self._active_vec.add_point(xy,window.view)

    def mouse_up(self, xy,window):
        if self._active_vec is not None:
            self._active_vec.finalize()
            self._manager.commit_vector(self._active_vec)
            self._active_vec = None


class Line(Pencil):
    def mouse_down(self, xy, window):
        self._active_vec = LineVec(*self._manger.get_color_thickness())
        self._active_vec.add_point(xy, window.view)

    

class Rectangle(Pencil):
    def mouse_down(self, xy, window):
        self._active_vec = RectangleVec(*self._manger.get_color_thickness())
        self._active_vec.add_point(xy, window.view)



class Circle(Pencil):
    def mouse_down(self, xy, window):
        self._active_vec = CircleVec(*self._manger.get_color_thickness())
        self._active_vec.add_point(xy, window.view)

class Pan(Tool):

    def __init__(self, tool_manager):
        super().__init__(tool_manager)
        self._panning_window = None
        
    def mouse_down(self, xy, window):
        self._panning_window = window
        window.start_pan(xy)

    def mouse_move(self, xy, window):
        if window != self._panning_window:
            raise Exception("Pan tool is being used in two windows at once.")
        window.pan(xy)

    def mouse_up(self, xy, window):
        if window != self._panning_window:
            raise Exception("Pan tool is being used in two windows at once.")
        window.end_pan()
        


class Select(Rectangle):
    def mouse_up(self, xy, window):
        print("User stopped selecting, finish this method...")
    

class ToolManager(object):
    # Manages anything user uses to change the whiteboard.
    _TOOLS = {'pencil': Pencil,
              'line': Line,
              'rectangle': Rectangle,
              'circle': Circle,
              'pan': Pan,
              'select': Select}

    def __init__(self, vector_manager, init_tool_name = 'pencil', init_color = 'black', init_thickness = 2):
        self._vectors = vector_manager
        self._color_n = init_color
        self._thickness = init_thickness 
        self.current_tool = None  # external access to current tool
        self._init_tools()
        self.switch_tool(init_tool_name)

    def commit_vector(self, vector):
        # send to server...
        self._vectors.add_vector(vector)
        
    def switch_tool(self, new_tool_name):
        if new_tool_name not in self._tools:
            ValueError(f'Invalid tool name (did you add to self._tools in _init_elements?): {new_tool_name}')
        self.current_tool = self._tools[new_tool_name]
        logging.info(f"Switched to tool: {new_tool_name}")

        
    def _init_tools(self):
        self._tools = {'pencil': Pencil(self),
                       'line': Line(self),
                       'rectangle': Rectangle(self),
                       'circle': Circle(self),
                       'pan': Pan(self),
                       'select': Select(self)}
        
        self._tool_list = list(self._tools.values())

    def set_color_thickness(self, color_name=None, thickness=None):
        self._color_n = color_name if color_name is not None else self._color_n
        self._thickness = thickness if thickness is not None else self._thickness
        logging.info(f"Color/thickness set to: {self._color_n}, {self._thickness}")

    def get_color_thickness(self):
        return self._color_n, self._thickness

    def render(self, img):
        pass
