
"""
Popup displays show the effects of changing a parameter while it's being adjusted (text size, line thickness, etc.).

"""
from abc import ABC, abstractmethod
import cv2
import numpy as np
from layout import COLORS_BGR, BOARD_LAYOUT, GRID_SPACING, SELECTION_BOX, EMPTY_BBOX
import logging
from util import expand_bbox, scale_points_to_bbox, floats_to_fixed
from gui_components import MouseReturnStates, Renderable
from vectors import TextVec

class PopupDisplay(Renderable, ABC):
    def __init__(self, name, window, margin_frac=0.2):
        """
        :param margin_frac: Fraction of the bbox to use as a margin.
        """

        self._draw_color_v = COLORS_BGR[BOARD_LAYOUT['obj_color']]
        self._bkg_v = COLORS_BGR[BOARD_LAYOUT['bkg_color']]
        self._bbox = self._get_bbox(window)
        self._margin_frac = margin_frac
        self._active = False
        self._name = name

        self._set_geom()
        self._set_window_gfx()

    def _get_bbox(self, window):
        # Determine where the display will show the value as its being changed.
        # For now, a rect in the middle of the window, 1/2 dims.
        ww, hw = window.get_size()
        w, h = ww//2, hw//2
        a_bbox = {'x': (w - w//2, w + w//2),
                  'y': (h - h//2, h + h//2)}
        return a_bbox
    
    def _set_window_gfx(self):
        w, h = self._bbox['x'][1] - self._bbox['x'][0], self._bbox['y'][1] - self._bbox['y'][0]
        self._bkg = np.zeros((h, w, 3), dtype=np.uint8)
        self._bkg[:, :] = self._bkg_v
        border_thickness =  4
        if border_thickness > 0:
            cv2.rectangle(self._bkg, (0, 0), (w, h), self._draw_color_v, border_thickness)

    def _render_bkg(self, img):
        x_min, x_max = self._bbox['x']
        y_min, y_max = self._bbox['y']
        img[y_min:y_max, x_min:x_max] = self._bkg

    @ abstractmethod
    def _set_geom(self):
        """
        Set the geometry of the popup display.
        """

    @ abstractmethod
    def render(self, img, disp_val):
        """
        Render the "value" the control wants displayed.
        """
        pass

    def get_bbox(self):
        return self._bbox

    def pop_up(self):
        #print("PopupDisplay %s pop_up" % self._name)
        self._active = True

    def pop_down(self):
        #print("PopupDisplay %s pop_down" % self._name)
        self._active = False


class ThicknessArtist(PopupDisplay):

    def _set_geom(self):
        x_min, x_max = self._bbox['x']
        y_min, y_max = self._bbox['y']

        w, h = x_max - x_min, y_max - y_min
        indent = int(w * self._margin_frac)
        self._line = (x_max - indent, y_min + indent), (x_min + indent, y_max - indent)
        self._text_loc = (x_min + indent, y_max - indent)
        self._text_size = 1

    def render(self, img, disp_val):
        self._render_bkg(img)
        cv2.line(img, self._line[0], self._line[1], self._draw_color_v, int(disp_val), cv2.LINE_AA)
        #cv2.putText(img, str(disp_val), self._text_loc, cv2.FONT_HERSHEY_SIMPLEX, self._text_size, self._draw_color_v)  

        
class TextSizeArtist(ThicknessArtist):

    def render(self, img, disp_val):
        self._render_bkg(img)
        print(disp_val)
        scale, thickness = TextVec.scale_and_thickness_from_size(disp_val)
        cv2.putText(img, "Scale %.2f" % disp_val, self._text_loc, cv2.FONT_HERSHEY_SIMPLEX, 
                    scale*2, self._draw_color_v, thickness=thickness) 