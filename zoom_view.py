"""
The ZoomViewControls are special controls.  Clicking/draging in their bbox's interior pans the zoom view
WRT the whiteboard.  They can be inside-out, so the "interior" is every part of the screen that is
NOT inside the bbox (as in the control window, where clicking in the box uses a tool to draw, but clicking
outside pans.)
"""
import numpy as np
from controls import Control
from layout import ZOOM_BOX, COLORS_BGR
from util import corners_to_bbox, move_bbox_to
from gui_components import MouseReturnStates
import cv2


class ZoomViewControl(Control):
    """
    A control that allows the user to pan the view of the whiteboard.
    """
    def __init__(self, window, name, bbox, inside_out=False, visible=True):
        """
        :param window: a UIWindow object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially
        """
        super().__init__(window, name, bbox, visible)
        self._color = COLORS_BGR[ZOOM_BOX['color']]
        self._thickness = ZOOM_BOX['thickness']
        self._inside_out = inside_out

    def in_bbox(self, xy):
        if self._inside_out:
            return not super().in_bbox(xy)
        else:
            return super().in_bbox(xy)
        
    def mouse_down(self, xy):
        self._window.start_pan(xy)
        return MouseReturnStates.captured
    
    def mouse_up(self, xy):
        self._window.end_pan()
        return MouseReturnStates.released
    
    def mouse_move(self, xy):
        self._window.pan_to(xy)
        return MouseReturnStates.captured
    
    def mouse_over(self, xy):
        pass
    
    def mouse_out(self):
        pass

    def render(self, frame, view):
        # Draw a box in self._bbox
        if self.visible:
            bbox_upper_left = self._bbox['x'][0], self._bbox['y'][0]
            bbox_lower_right = self._bbox['x'][1], self._bbox['y'][1]
            cv2.rectangle(frame, bbox_upper_left, bbox_lower_right, self._color, self._thickness, lineType=cv2.LINE_AA)
        