"""
Slider tool.  User moves a box along a line to choose a value.
"""

import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS
import logging
from util import get_font_size, in_bbox, is_numeric, draw_bbox
from controls import Control
from gui_components import MouseReturnStates


def value_from_position(values, position, interpolate=True):
    """
    :param values: list of values to choose from, left to right or top to bottom.
    :param position: float in [0, 1], position of the slider tab.
    :param interpolate: bool, if True, interpolate between values based on slider position, else use the closest value.
    :returns: value (interpolated/selected value)
    """
    if interpolate:
        value_x = np.linspace(0, 1, len(values))
        val = np.interp(position, value_x, values)
    else:
        val = values[int(np.round(position * (len(values) - 1)))]
    return val

def position_from_value(values, value, interpolate=True):
    """
    :param values: list of values to choose from, left to right or top to bottom.
    :param value: float, value to find on the slider.
    :param interpolate: bool, if True, interpolate between values based on slider position, else use the closest value.
    :returns: position (float in [0, 1], position of the slider tab.
    """
    if interpolate:
        value_x = np.linspace(0, 1, len(values))
        position = np.interp(value, values, value_x)
    else:
        position = values.index(value) / (len(values) - 1)
    return position




class Slider(Control):
    def __init__(self, board, bbox, name, orientation='horizontal', values=[1.0, 10.], label_str="%s",
                  interpolate=True, init_val=0.5, visible=True, show_bbox=False, valchange_callbacks=()):
        """
        :param board: Board object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param name: widget name
        :param orientation: str, 'horizontal' or 'vertical'
        :param values: list of values to choose from, left to right or top to bottom.
            The elments of this list are spaced evenly along the length of the slider, and:
               - if they are numeric and interpolate is True, the returned value is interpolated based on slider position, or
               - else, the closest value is returned.
        :param label_str: str, label format string, e.g. "Threshold: %s"
        :param interpolate: bool, if True, interpolate between values based on slider position, else use the closest value.
        :param init_pos: float, initial position of the slider, reletive to endpoints.
        """
        self._callbacks = valchange_callbacks
        self._label = label_str
        self._show_bbox = show_bbox
        self._orientation = orientation
        self._values = values
        self._interpolate = interpolate
        if interpolate and not is_numeric(values):
            logging.warning("Interpolation requested but values are not numeric.  Interpolation will be disabled.")
            self._interpolate = False

        # state
        self._cur_value_rel = position_from_value(values,init_val)  # stores current position of slider tab
        self._obj_color_v = COLORS_RGB[SLIDERS['line_color']]
        self._line_thickness = SLIDERS['line_thickness']
        self._label_font = SLIDERS['label_font']
        self._line_color = COLORS_RGB[SLIDERS['line_color']]
        self._tab_color = COLORS_RGB[SLIDERS['tab_color']]
        self._label_color = COLORS_RGB[SLIDERS['label_color']]

        super().__init__(board, name, bbox, visible)
        logging.info("Created %s slider '%s' in bbox %s, will display like:  %s." % (orientation, name, bbox, self._get_disp_str()))

        # calls self._set_geom()
    def _get_disp_str(self,val=None):
        val = val if val is not None else self.get_value()
        return self._label % val
    
    def _set_geom(self):

        # define absolute geometry (WRT window pixels) from relative in layout.py:
        x_min, x_max = self._bbox['x']
        y_min, y_max = self._bbox['y']
        w, h = x_max - x_min, y_max - y_min

        self._font_scale, self._font_thickness = get_font_size(self._bbox, self._orientation)
        label_width, label_height = self._get_max_label_dims()

        tab_wh_rel = SLIDERS['tab_width'], SLIDERS['tab_height']

        if self._orientation == 'horizontal':

            self._margin_px = SLIDERS['indent'] * w

            # tab dimensions
            self._tab_wh = w * tab_wh_rel[0], h * tab_wh_rel[1]
            # line dimensions
            y_center = (y_min + y_max) // 2

            length = w - label_width - 3 * self._margin_px
            x = x_min + label_width + 2*self._margin_px
            self._line_endpoints = np.array([[x, y_center], [x + length, y_center]])
            self._label_spacing = self._margin_px

        else:

            self._margin_px = SLIDERS['indent'] * h
            # tab dimensions
            self._tab_wh = h * tab_wh_rel[0], w * tab_wh_rel[1]
            # line dimensions
            x_center = (x_min + x_max) // 2
            length = h - label_height - 3 * self._margin_px
            y = y_min + label_height + 2 * self._margin_px
            self._line_endpoints = np.array([[x_center, y], [x_center, y + length]])
            self._label_spacing = self._margin_px
        self._line_endpoints = np.array(self._line_endpoints, dtype=np.int32)

    def __str__(self):
        return "Slider '%s' in bbox %s" % (self._label, self._bbox)

    def get_tab_pos(self):
        """
        Get the bounding box of the tab.
        """
        if self._orientation == 'horizontal':
            x_min, x_max = self._line_endpoints[0, 0], self._line_endpoints[1, 0]
            x = x_min + self._cur_value_rel * (x_max - x_min)
            y = self._line_endpoints[0, 1]
            w, h = self._tab_wh
        else:
            y_min, y_max = self._line_endpoints[0, 1], self._line_endpoints[1, 1]
            x = self._line_endpoints[0, 0]
            y = y_min + self._cur_value_rel * (y_max - y_min)
            w, h = self._tab_wh[::-1]
        return {'x': (x-w//2, x + w//2),
                'y': (y-h//2, y + h//2)}

    def render(self, img):
        """
        Draw the slider on the image:
            * A line represents the possible positions of the slider
            * A box represents the current position of the slider
            * "label:  value" is displayed to the left of the line, or above the box, depending on self.orientation
        """
        # draw line first
        cv2.line(img, tuple(self._line_endpoints[0, :]), tuple(
            self._line_endpoints[1, :]), self._line_color, self._line_thickness)
        # draw tab
        tab_pos = self.get_tab_pos()
        tab_p1 = (int(tab_pos['x'][0]), int(tab_pos['y'][0]))
        tab_p2 = (int(tab_pos['x'][1]), int(tab_pos['y'][1]))
        cv2.rectangle(img, tab_p1, tab_p2, self._tab_color, -1)
        # draw label
        label = self._get_disp_str()
        (width, height), _ = cv2.getTextSize(label, self._label_font, self._font_scale, self._font_thickness)

        if self._orientation == 'horizontal':
            x = int(self._line_endpoints[0, 0] - self._label_spacing - width)
            y = int(self._line_endpoints[0, 1] + height // 2)
        else:
            x = int(self._line_endpoints[0, 0] - width // 2)
            y = int(self._line_endpoints[0, 1] - self._label_spacing)
        cv2.putText(img, label, (x, y), self._label_font, self._font_scale, self._label_color, self._font_thickness,
                    lineType=cv2.LINE_AA)

        if self._show_bbox:
            draw_bbox(img, self._bbox, self._obj_color_v, 1)

    def _click_to_rel_value(self, xy_px):
        """
        :param xy_px: tuple of x, y pixel coordinates where the mouse moved
        :returns: float in [0, 1], e.g. 0 if x < (left-endpoint of horizontal line), ...
        """
        if self._orientation == 'horizontal':
            lo, hi = self._line_endpoints[0, 0], self._line_endpoints[1, 0]
            val = xy_px[0]
        else:
            lo, hi = self._line_endpoints[0, 1], self._line_endpoints[1, 1]
            val = xy_px[1]
        t = (val - lo) / (hi - lo)
        return max(0., min(1., t))

    def get_value(self, rel_val=None):
        """
        Get the value & str of the slider.
        :param rel_val: float in [0, 1], if None, use self._cur_value_rel
        :returns: value (interpolated/selected value),
                  character representation of value
        """
        rel_val = self._cur_value_rel if rel_val is None else rel_val
        return value_from_position(self._values, rel_val, self._interpolate)

    def _get_max_label_dims(self):
        """
        Set 1000 random values and return the biggest label dimensions.
        """
        max_width, max_height = 0, 0
        for i in range(1000):
            label = self._get_disp_str(val=self.get_value(rel_val=np.random.rand()))
            (width, height), _ = cv2.getTextSize(label, self._label_font, self._font_scale, self._font_thickness)
            max_width = max(max_width, width)
            max_height = max(max_height, height)
        return max_width, max_height

    def mouse_down(self, xy):
        self._cur_value_rel = self._click_to_rel_value(xy)
        self._do_callbacks()
        return self._capture_mouse()

    def mouse_up(self, xy):
        return self._release_mouse()

    def mouse_move(self, xy):
        self._cur_value_rel = self._click_to_rel_value(xy)
        self._do_callbacks()
        return MouseReturnStates.captured

    def _do_callbacks(self):
        val = self.get_value()

        for callback in self._callbacks:

            callback(val)


