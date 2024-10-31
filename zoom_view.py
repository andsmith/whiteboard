"""
The ZoomViewControls are special controls.  Clicking/draging in their bbox's interior pans the zoom view
WRT the whiteboard.  They can be inside-out, so the "interior" is every part of the screen that is
NOT inside the bbox (as in the control window, where clicking in the box uses a tool to draw, but clicking
outside pans.)
"""
import numpy as np
from controls import Control
from util import corners_to_bbox, move_bbox_to




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
        self._inside_out = inside_out
        self._set_geom()
        self._init_semantics()

    def _set_geom(self):
        pass
    def _init_semantics(self):
        self._pan = False