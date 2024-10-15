from gui_components import GUIArtist
from layout import COLORS_BGR, CONTROL_LAYOUT, BOARD_LAYOUT
import logging
import cv2
import numpy as np
from util import in_bbox, get_circle_points, floats_to_fixed, PREC_BITS
from abc import ABC, abstractmethod
import json


def load_scribble():
    with open('assets/unit_scribble.json', 'r') as infile:
        return np.array(json.load(infile))


CTRL_PT_COLORS_BGR = {'outer': COLORS_BGR['black'],
                      'inner': COLORS_BGR['white']}
ICON_MARGIN_FRAC = 0.3
UNIT_SCRIBBLE_COORDS = load_scribble()


class IconArtist(GUIArtist, ABC):
    """
    Draw a simple shape in a bounding box.
    """

    def __init__(self, board, bbox):
        super().__init__(board, bbox)
        self._color = COLORS_BGR[board.default_color]
        self._set_geom()

    @abstractmethod
    def _set_geom(self):
        # self._bbox was just set, so update internal geometry.
        pass

    def _draw_ctrl_point(self, img, ctrl_point, outer_size=3, inner_size=1):
        """
        Draw a control point on the image.
        A control point is a black square around the point, with the center pixel the color.
        """
        x, y = ctrl_point
        x, y = int(x), int(y)
        cv2.rectangle(img, (x - outer_size, y - outer_size), (x + outer_size, y + outer_size),
                      CTRL_PT_COLORS_BGR['outer'], -1)
        cv2.rectangle(img, (x - inner_size, y - inner_size), (x + inner_size, y + inner_size),
                      CTRL_PT_COLORS_BGR['inner'], -1)

    def boxed_render(self, img):
        """
        Draw the icon on the image w/ a bounding box.
        """
        cv2.rectangle(img, (self._bbox['x'][0], self._bbox['y'][0]),
                      (self._bbox['x'][1], self._bbox['y'][1]), self._color, 1)
        self.render(img)


class CircleIcon(IconArtist):
    """
    Draw a circle taking up the whole bounding box, minus the margin.
    """

    def _set_geom(self):
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        full_rad = min(x_max - x_min, y_max - y_min)/2
        self._center = (x_min + (x_max - x_min) / 2, y_min + (y_max - y_min) / 2)
        rad = full_rad * (1.0 - ICON_MARGIN_FRAC)
        self._points = get_circle_points(self._center, rad)
        self._ctrl_point1 = self._points[0]
        self._ctrl_point2 = self._center

    def render(self, img):
        """
        Draw the unfilled circle, with the control points.
        """
        cv2.polylines(img, [floats_to_fixed(self._points)], True,
                      self._color, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        self._draw_ctrl_point(img, self._ctrl_point1)
        self._draw_ctrl_point(img, self._ctrl_point2)


class LineIcon(IconArtist):
    """
    Draw a line scaled to a smaller square within the unit square (i.e. for the margin)
    show control points at each end
    """

    def _set_geom(self):
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        line_coords_rel = np.array([(0.2, 0), (0.6, 1)]) * (1.0 - ICON_MARGIN_FRAC)
        # center
        line_coords_rel += np.array([0.5, 0.5]) * ICON_MARGIN_FRAC
        self._points = np.array([(x_min + x * (x_max - x_min), y_min + y * (y_max - y_min))
                                 for x, y in line_coords_rel])
        self._ctrl_point1 = self._points[0]
        self._ctrl_point2 = self._points[1]

    def render(self, img):
        """
        Draw the line and control points.
        """
        cv2.polylines(img, [floats_to_fixed(self._points)], False,
                      self._color, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        self._draw_ctrl_point(img, self._ctrl_point1)
        self._draw_ctrl_point(img, self._ctrl_point2)


class RectangleIcon(CircleIcon):
    """
    Draw a rectangle in the bbox , with control points at opposite corners.
    """

    def _set_geom(self):
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        x_pad, y_pad = (x_max - x_min) * ICON_MARGIN_FRAC/2, (y_max - y_min) * ICON_MARGIN_FRAC/2
        x_min += x_pad
        x_max -= x_pad
        y_min += y_pad
        y_max -= y_pad
        self._points = np.array([(x_min, y_min), (x_max, y_min),
                                 (x_max, y_max), (x_min, y_max)])
        self._ctrl_point1 = self._points[0]
        self._ctrl_point2 = self._points[2]


def _scale_points_to_bbox(unit_points, bbox, margin_frac=ICON_MARGIN_FRAC):
    """
    Fit the points in the bounding box, padded by a margin.


    :param unit_points: Nx2 array of points in the unit square
    :param bbox: {x:(x_min, x_max), y:(y_min, y_max)} bounding box (pixels) points will ultimately be drawn in.
    :param margin_frac: fraction of the unit square to leave as a margin (points are shrunk by 1-margin_frac)
    :returns: Nx2 array of points in the bounding box ready to plot (int32).
    """
    x_min, x_max = bbox['x']
    y_min, y_max = bbox['y']
    x_pad = (x_max - x_min) * margin_frac / 2
    y_pad = (y_max - y_min) * margin_frac / 2
    x_min += x_pad
    x_max -= x_pad
    y_min += y_pad
    y_max -= y_pad
    x_scale = x_max - x_min
    y_scale = y_max - y_min
    return floats_to_fixed(np.array([(x_min + x * x_scale, 
                                      y_min + y * y_scale)
                                     for x, y in unit_points]))


class PencilIcon(CircleIcon):
    """
    Load the "scribble" coordinates, scale to unit square, and draw the scribble.
    The control points are the first and last points.
    """

    def _set_geom(self):
        # scale to unit square
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        x_scale = x_max - x_min
        y_scale = y_max - y_min
        points = UNIT_SCRIBBLE_COORDS * (1.0 - ICON_MARGIN_FRAC)
        points += np.array([0.5, 0.5]) * ICON_MARGIN_FRAC
        self._points = np.array([(x_min + x * x_scale, y_min + y * y_scale)
                                 for x, y in points])
        self._ctrl_point1 = self._points[0]
        self._ctrl_point2 = self._points[-1]

    def render(self, img):
        cv2.polylines(img, [floats_to_fixed(self._points)], False,
                      self._color, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        self._draw_ctrl_point(img, self._ctrl_point1)
        self._draw_ctrl_point(img, self._ctrl_point2)


class PanIcon(IconArtist):
    # Four arrows pointing in the cardinal directions.
    def _set_geom(self):
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        x_center = x_min + (x_max - x_min) / 2
        y_center = y_min + (y_max - y_min) / 2
        arrow_spread = 0.1
        arrowhead_len = 0.2
        center = (0.5, 0.5)
        # arrow from center to top of unit square:
        up_rel = {'tip': (0.5, 1.0),
                  'left': (0.5-arrow_spread, 1.0-arrowhead_len),
                  'right': (0.5 + arrow_spread, 1.0-arrowhead_len)}
        down_rel = {'tip': (0.5, 0.0),
                    'left': (0.5-arrow_spread, arrowhead_len),
                    'right': (0.5 + arrow_spread, arrowhead_len)}
        left_rel = {'tip': (0.0, 0.5),
                    'left': (arrowhead_len, 0.5-arrow_spread),
                    'right': (arrowhead_len, 0.5 + arrow_spread)}
        right_rel = {'tip': (1.0, 0.5),
                     'left': (1.0-arrowhead_len, 0.5-arrow_spread),
                     'right': (1.0-arrowhead_len, 0.5 + arrow_spread)}

        def get_arrow_lines(arrow):
            return [[arrow['tip'], center],
                    [arrow['left'], arrow['tip'], arrow['right']]]
        rel_lines = get_arrow_lines(up_rel) + get_arrow_lines(down_rel) + \
            get_arrow_lines(left_rel) + get_arrow_lines(right_rel)

        # now scale to the bounding box

        lines = [_scale_points_to_bbox(np.array(rel_line), self._bbox) for rel_line in rel_lines]
        
        self._fixed_lines = lines

    def render(self, img):
        cv2.polylines(img, self._fixed_lines, False,
                      self._color, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)


class SelectIcon(IconArtist):
    pass


# keys should match ToolManager._TOOLS.keys() so buttons can see both.
BUTTON_ARTISTS = {'circle': CircleIcon,
                  'rectangle': RectangleIcon,
                  'line': LineIcon,
                  'pencil': PencilIcon,
                  'pan': PanIcon,
                  'select': SelectIcon}


class FakeBoard:
    def __init__(self):
        self.default_color = BOARD_LAYOUT['obj_color']


def test_icon_artists():
    img = (np.zeros((100, 600, 3)) + COLORS_BGR[BOARD_LAYOUT['bkg_color']]).astype(np.uint8)
    circle = CircleIcon(FakeBoard(), {'x': (10, 70), 'y': (10, 80)})
    line = LineIcon(FakeBoard(), {'x': (110, 170), 'y': (10, 80)})
    pencil = PencilIcon(FakeBoard(), {'x': (210, 270), 'y': (10, 80)})
    rectangle = RectangleIcon(FakeBoard(), {'x': (310, 370), 'y': (10, 80)})
    pan = PanIcon(FakeBoard(), {'x': (410, 470), 'y': (10, 80)})

    circle.boxed_render(img)
    line.boxed_render(img)
    pencil.boxed_render(img)
    rectangle.boxed_render(img)
    pan.boxed_render(img)

    cv2.imshow('circle', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    test_icon_artists()
