from gui_components import GUIArtist
from layout import COLORS_BGR, CONTROL_LAYOUT, BOARD_LAYOUT
import logging
import cv2
import numpy as np
from util import in_bbox, get_circle_points, floats_to_fixed, PREC_BITS, scale_points_to_bbox, PREC_SCALE
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
        self._lines = []  # list of np.int32 arrays of points (each is an Nx2 polyline)  
        self._ctrl_points = []  # list of control points (Cx2)
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

    def render(self, img):
        """
        Draw the unfilled circle, with the control points.
        """
        cv2.polylines(img, self._lines , True,
                      self._color, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        for ctrl_point in self._ctrl_points:
            self._draw_ctrl_point(img, ctrl_point)

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
        points = get_circle_points(self._center, rad)
        self._lines = [floats_to_fixed(points)]
        self._ctrl_points = [points[0], self._center]


class LineIcon(IconArtist):
    """
    Draw a line scaled to a smaller square within the unit square (i.e. for the margin)
    show control points at each end
    """

    def _set_geom(self):
        line_coords_rel = np.array([(0.2, 0), (0.6, 1)]) 
        line_coords = scale_points_to_bbox(line_coords_rel, self._bbox)
        self._lines = [floats_to_fixed(line_coords)]
        
        self._ctrl_points = [line_coords[0],line_coords[1]]
        
class RectangleIcon(CircleIcon):
    """
    Draw a rectangle in the bbox , with control points at opposite corners.
    """

    def _set_geom(self):
        corners = [(0,0), (1,0), (1,1), (0,1)]
        corner_points = scale_points_to_bbox(np.array(corners,dtype=np.float64), self._bbox)
        
        self._lines = [floats_to_fixed(corner_points)]
        self._ctrl_points = [corner_points[0], corner_points[2]]


class PencilIcon(CircleIcon):
    """
    Load the "scribble" coordinates, scale to unit square, and draw the scribble.
    The control points are the first and last points.
    """

    def _set_geom(self):
        # scale to unit square
        
        points = UNIT_SCRIBBLE_COORDS
        points = scale_points_to_bbox(points, self._bbox)
        self._lines = [floats_to_fixed(points)]
        self._ctrl_point1 = points[0]
        self._ctrl_point2 = points[-1]

    def render(self, img):
        cv2.polylines(img, self._lines, False,
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

        self._lines = [floats_to_fixed(scale_points_to_bbox(np.array(rel_line), self._bbox)) for rel_line in rel_lines]
        self._ctrl_points = [(x_center, y_center)]


class SelectIcon(RectangleIcon):
    # A rectangle with a dashed line, control points at opposite_corners.
    _N_DASHES = 6  # A line is broken into this many black segments

    def _set_geom(self):
        # Create RectangleIcon geometry, break the lines into dashed lines.
        super()._set_geom()
        solid_lines = self._lines[0]
        p1, p2 = solid_lines[0], solid_lines[2]  # top left, bottom right  
        dash_breaks = np.linspace(0, 1, self._N_DASHES * 2)
        x = p1[0] + (p2[0] - p1[0]) * dash_breaks
        y = p1[1] + (p2[1] - p1[1]) * dash_breaks
        top_segments = [((x[i], y[0]), (x[i+1], y[0])) for i in range(0, len(x), 2)]
        bottom_segments = [((x[i], y[-1]), (x[i+1], y[-1])) for i in range(0, len(x), 2)]
        left_segments = [((x[0], y[i]), (x[0], y[i+1])) for i in range(0, len(y), 2)]
        right_segments = [((x[-1], y[i]), (x[-1], y[i+1])) for i in range(0, len(y), 2)]
        lines = top_segments + left_segments + right_segments+ bottom_segments
        self._lines = [np.array(line,dtype=np.int32) for line in lines]
        fixed_ctrl_points = [top_segments[0][0], bottom_segments[-1][1]]
        # these are not stored as fixed-point numbers, make them floats again:
        self._ctrl_points = [(x/PREC_SCALE, y/PREC_SCALE) for x, y in fixed_ctrl_points]
    
    
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
    img = (np.zeros((150, 600, 3)) + COLORS_BGR[BOARD_LAYOUT['bkg_color']]).astype(np.uint8)
    circle = CircleIcon(FakeBoard(), {'x': (10, 70), 'y': (10, 80)})
    line = LineIcon(FakeBoard(), {'x': (110, 170), 'y': (10, 80)})    

    pencil = PencilIcon(FakeBoard(), {'x': (210, 270), 'y': (10, 80)})
    rectangle = RectangleIcon(FakeBoard(), {'x': (310, 370), 'y': (10, 80)})
    pan = PanIcon(FakeBoard(), {'x': (410, 470), 'y': (10, 80)})
    select = SelectIcon(FakeBoard(), {'x': (510, 570), 'y': (10, 80)})

    circle.boxed_render(img)
    line.boxed_render(img)
    pencil.boxed_render(img)
    rectangle.boxed_render(img)
    pan.boxed_render(img)
    select.boxed_render(img)

    cv2.imshow('circle', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    test_icon_artists()
