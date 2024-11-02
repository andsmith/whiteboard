from gui_components import MouseReturnStates
from abc import ABC, abstractmethod
import cv2
import numpy as np
from vectors import PencilVec, LineVec, RectangleVec, CircleVec
from layout import COLORS_RGB, CONTROL_LAYOUT, GRID_SPACING
import logging


class Tool(ABC):
    """
    things used to create different kinds of vector objects or manipulate them (pencil, line, ...)
    """

    def __init__(self, tool_manager, vector_manager):
        self._manager = tool_manager
        self._vecs = vector_manager
        self._active_vec = None  # the vector being created by the user

    @abstractmethod
    def mouse_down(self, xy, window):
        """
        Starting to use the tool.
        :param xy: (x, y) position of mouse in pixels
        :param window: UIWindow object mouse clicked in.
        """
        pass # NOTE:  Don't forget to return the correct MouseReturnStates

    @abstractmethod
    def mouse_move(self, xy, window):
        pass # and here... 

    @abstractmethod
    def mouse_up(self, xy, window):
        pass  # and here too.

    def render(self, img):
        # TODO:  Render cursors here?
        pass

class Pencil(Tool):
    def mouse_down(self, xy, window):
        print("Pencil mouse down")
        self._active_vec = PencilVec(*self._manager.get_color_thickness())
        self._active_vec.add_point(xy, window.view)
        self._vecs.start_vector(self._active_vec)
        return MouseReturnStates.captured

    def mouse_move(self, xy, window):
        if self._active_vec is not None:
            self._active_vec.add_point(xy, window.view)
        return MouseReturnStates.captured

    def mouse_up(self, xy, window):
        if self._active_vec is not None:
            self._active_vec.finalize()
            self._vecs.finish_vector()
            self._active_vec = None
        return MouseReturnStates.released


class Line(Pencil):
    def __init__(self, tool_manager, vector_manager):
        super().__init__(tool_manager, vector_manager)
        self._last_grid_point = None

    def _get_nearest_grid_point(self, xy, view):
        # For now use global (smallest) grid spacing
        grid_spacing = GRID_SPACING[0]
        xy_board = view.pts_from_pixels(xy)
        grid_x = round(xy_board[0] / grid_spacing) * grid_spacing
        grid_y = round(xy_board[1] / grid_spacing) * grid_spacing
        return view.pts_to_pixels((grid_x, grid_y))
    
    def _get_and_check_grid_point(self, xy, view):
        if self._manager.app.get_option('snap_to_grid'):
            xy = self._get_nearest_grid_point(xy, view)  
            if self._last_grid_point is not None and np.all(xy == self._last_grid_point):
                return None
            self._last_grid_point = xy
        return xy

    def mouse_down(self, xy, window):
        xy = self._get_and_check_grid_point(xy, window.view)
        if xy is None:
            return MouseReturnStates.captured
        self._active_vec = LineVec(*self._manager.get_color_thickness())
        self._active_vec.add_point(xy, window.view)
        self._active_vec.add_point(xy, window.view)  # add the same point twice to start
        self._vecs.start_vector(self._active_vec)
        return MouseReturnStates.captured



    def mouse_move(self, xy, window):
        if self._active_vec is not None:
            xy = self._get_and_check_grid_point(xy, window.view)
            if xy is None:
                return MouseReturnStates.captured
            print("ADDING POINT", xy)
            self._active_vec.add_point(xy, window.view)
        return MouseReturnStates.captured
    

class Rectangle(Line):
    def mouse_down(self, xy, window):
        if self._manager.app.get_option('snap_to_grid'):
            xy = self._get_nearest_grid_point(xy, window.view)  
        self._last_grid_point = xy
        self._active_vec = RectangleVec(*self._manager.get_color_thickness())
        self._active_vec.add_point(xy, window.view)
        self._vecs.start_vector(self._active_vec)

        return MouseReturnStates.captured


class Circle(Line):
    def mouse_down(self, xy, window):
        if self._manager.app.get_option('snap_to_grid'):
            xy = self._get_nearest_grid_point(xy, window.view)  
        self._last_grid_point = xy
        self._active_vec = CircleVec(*self._manager.get_color_thickness())
        self._active_vec.add_point(xy, window.view)
        self._vecs.start_vector(self._active_vec)

        return MouseReturnStates.captured


class Pan(Tool):

    def __init__(self, tool_manager, vector_manager):
        super().__init__(tool_manager, vector_manager)
        self._panning_window = None

    def mouse_down(self, xy, window):
        self._panning_window = window
        window.start_pan(xy)
        return MouseReturnStates.captured

    def mouse_move(self, xy, window):
        if window != self._panning_window:
            raise Exception("Pan tool is being used in two windows at once.")
        window.pan_to(xy)
        return MouseReturnStates.captured

    def mouse_up(self, xy, window):
        if window != self._panning_window:
            raise Exception("Pan tool is being used in two windows at once.")
        window.end_pan()
        return MouseReturnStates.released


class Select(Rectangle):

    def __init__(self, tool_manager, vector_manager):
        super().__init__(tool_manager, vector_manager)
        self._selected = None

    def mouse_up(self, xy, window):
        print("User stopped selecting, finish this method...")
        return MouseReturnStates.released


class ToolManager(object):
    # Manages anything user uses to change the whiteboard.
    _TOOLS = {'pencil': Pencil,
              'line': Line,
              'rectangle': Rectangle,
              'circle': Circle,
              'pan': Pan,
              'select': Select}

    def __init__(self, app, vector_manager, init_tool_name='pencil', init_color='black', init_thickness=2):
        self.vectors = vector_manager
        self.app = app
        self._color_n = init_color
        self._thickness = init_thickness
        self.current_tool = None  # external access to current tool
        self._init_tools()
        self.switch_tool(init_tool_name)

    def switch_tool(self, new_tool_name):
        if new_tool_name not in self._tools:
            ValueError(f'Invalid tool name (did you add to self._tools in _init_elements?): {new_tool_name}')
        self.current_tool = self._tools[new_tool_name]
        logging.info(f"Switched to tool: {new_tool_name}")

    def _init_tools(self):
        self._tools = {'pencil': Pencil(self, self.vectors),
                       'line': Line(self,self.vectors),
                       'rectangle': Rectangle(self,self.vectors),
                       'circle': Circle(self,self.vectors),
                       'pan': Pan(self, self.vectors),
                       'select': Select(self,self.vectors),}

        self._tool_list = list(self._tools.values())

    def set_color_thickness(self, color_name=None, thickness=None):
        self._color_n = color_name if color_name is not None else self._color_n
        self._thickness = thickness if thickness is not None else self._thickness
        logging.info(f"Color/thickness set to: {self._color_n}, {self._thickness}")

    def get_color_thickness(self):
        return self._color_n, self._thickness

    def render(self, img):
        self.current_tool.render(img)
