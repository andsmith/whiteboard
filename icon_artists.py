from gui_components import Renderable
from layout import COLORS_BGR, BOARD_LAYOUT, DEFAULT_ICON_MARGIN_FRAC
import logging
import cv2
import numpy as np
from util import (in_bbox, get_circle_points, floats_to_fixed, PREC_BITS, translate_lines,
                  scale_points_to_bbox, PREC_SCALE, get_text_cursor_points)
from abc import ABC, abstractmethod
import json


def load_scribble():
    with open('assets/unit_scribble.json', 'r') as infile:
        return np.array(json.load(infile))


CTRL_PT_COLORS_BGR = {'outer': COLORS_BGR['black'],
                      'inner': COLORS_BGR['white']}

UNIT_SCRIBBLE_COORDS = load_scribble()


class IconArtist(Renderable, ABC):
    """
    Draw a simple shape in a bounding box.
    """

    def __init__(self, bbox, margin_frac=None, draw_filled=False, closed=True):
        """
        :param margin_frac: float, fraction of the bounding box to leave as margin when drawing icon.
        """
        self._margin_frac = margin_frac if margin_frac is not None else DEFAULT_ICON_MARGIN_FRAC

        super().__init__(self._get_name(), bbox)
        self._obj_color_v = COLORS_BGR[BOARD_LAYOUT['obj_color']]  # parts of icon drawn whose color doesn't change
        self._bkg_color_v = COLORS_BGR[BOARD_LAYOUT['bkg_color']]  # parts of icon drawn whose color doesn't change
        self.color_v = COLORS_BGR[BOARD_LAYOUT['obj_color']]  # parts of icon need to be drawn in this color
        faintness = 0.4
        self._faint_color_v = (faintness * np.array(self._obj_color_v) +
                               (1.0-faintness) * np.array(self._bkg_color_v)).tolist()
        self._lines = []  # list of np.int32 arrays of points (each is an Nx2 polyline)
        self._ctrl_points = []  # list of control points (Cx2)
        self._filled = draw_filled
        self._closed = closed
        self._set_geom()

    @classmethod
    def _get_name(cls):
        return cls.__name__.replace('Icon', '').lower()

    def move_to(self, xy, new_bbox=None):
        """
        Translate or set a new bbox.
        """
        if new_bbox is not None:
            self._bbox = new_bbox
        else:
            x_span, y_span = self._bbox['x'][1] - self._bbox['x'][0], self._bbox['y'][1] - self._bbox['y'][0]
            self._bbox = {'x': (xy[0], xy[0] + x_span), 'y': (xy[1], xy[1] + y_span)}
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

    def boxed_render(self, img, held=False, moused_over=False):
        """
        Draw the icon on the image w/ a bounding box.
        """
        cv2.rectangle(img, (self._bbox['x'][0], self._bbox['y'][0]),
                      (self._bbox['x'][1], self._bbox['y'][1]), self._obj_color_v, 1)
        return self.render(img, held, moused_over)

    def render(self, img, held=False, moused_over=False):
        """
        Draw the shape & control points.
        """
        thickness = 1 if not held else 2
        if self._filled:
            cv2.fillPoly(img, self._lines, self.color_v, lineType=cv2.LINE_AA, shift=PREC_BITS)
        else:
            cv2.polylines(img, self._lines, self._closed, self.color_v,
                          lineType=cv2.LINE_AA, thickness=thickness, shift=PREC_BITS)
        for ctrl_point in self._ctrl_points:
            self._draw_ctrl_point(img, ctrl_point)


class CircleToolIcon(IconArtist):
    """
    Draw a circle taking up the whole bounding box, minus the margin.
    """

    def _get_perimiter(self):
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        full_rad = min(x_max - x_min, y_max - y_min)/2
        self._center = (x_min + (x_max - x_min) / 2, y_min + (y_max - y_min) / 2)
        rad = full_rad * (1.0 - self._margin_frac)
        return get_circle_points(self._center, rad)

    def _set_geom(self):
        points = self._get_perimiter()
        self._lines = [floats_to_fixed(points)]
        self._ctrl_points = [points[0], self._center]


class SnapToGridIcon(CircleToolIcon):

    """
    3x3 grid of lines, with a heavy line from (2,)"""

    def __init__(self, bbox, margin_frac=None):
        self._heavy_lines = []
        self._faint_lines = []
        super().__init__(bbox, margin_frac)

    def _set_geom(self):
        n_lines = 6
        x_grid, y_grid = np.linspace(0., 1., n_lines), np.linspace(0., 1., n_lines)

        vertical_lines = [np.array(((x, 0), (x, 1))) for x in x_grid]
        horizontal_lines = [np.array(((0, y), (1, y))) for y in y_grid]
        self._ctrl_points = scale_points_to_bbox(np.array([(x_grid[2], y_grid[1]),
                                                           (x_grid[4], y_grid[4]),
                                                           (x_grid[4], y_grid[1]),
                                                           (x_grid[1], y_grid[4]),
                                                           (x_grid[4], y_grid[4])]), self._bbox, margin_frac=self._margin_frac)

        ctrl_lines = [np.array((self._ctrl_points[i], self._ctrl_points[i+1])) for i in range(len(self._ctrl_points)-1)]

        self._heavy_lines = [floats_to_fixed(line) for line in ctrl_lines]
        self._faint_lines = [floats_to_fixed(scale_points_to_bbox(line,
                                                                  self._bbox,
                                                                  margin_frac=self._margin_frac))
                             for line in vertical_lines[1:-1] + horizontal_lines[1:-1]]

    def render(self, img, held=False, moused_over=False):
        cv2.polylines(img, self._faint_lines, False, self._faint_color_v,
                      lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        cv2.polylines(img, self._heavy_lines, False, self._obj_color_v,
                      lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        # print(np.mean(self._heavy_lines[0], axis=0)), np.mean(self._faint_lines[0], axis=0)
        for ctrl_point in self._ctrl_points:
            self._draw_ctrl_point(img, ctrl_point)  # for subclass


class GridIcon(SnapToGridIcon):
    """
    Icon that turns off/on the background grid.
    (Should be a small grid, clipped to within a cirlce)
    """

    def _set_geom(self):
        self._ctrl_points = []  # none of these to draw
        circle = self._get_perimiter()

        x_min, x_max = np.min(circle, axis=0)[0], np.max(circle, axis=0)[0]
        y_min, y_max = np.min(circle, axis=0)[1], np.max(circle, axis=0)[1]
        n_lines = 5
        heavy_modulus = 3
        heavy_lines = []
        faint_lines = []
        for i in range(n_lines):
            frac = i / n_lines
            x = x_min + (x_max - x_min) * frac
            y = y_min + (y_max - y_min) * frac
            if i % heavy_modulus == 0:
                heavy_lines.append([(x_min, y), (x_max, y)])
                heavy_lines.append([(x, y_min), (x, y_max)])
            else:
                faint_lines.append([(x_min, y), (x_max, y)])
                faint_lines.append([(x, y_min), (x, y_max)])

        self._heavy_lines = [floats_to_fixed(np.array(line, dtype=np.float64)) for line in heavy_lines]
        self._faint_lines = [floats_to_fixed(np.array(line, dtype=np.float64)) for line in faint_lines]


class ClearIcon(SnapToGridIcon):
    """
    A rectangular "window" with a big X in it.
    """

    def _correct_lines(self, lines):
        lines = scale_points_to_bbox(np.array(lines, dtype=np.float64), self._bbox, margin_frac=self._margin_frac)
        return floats_to_fixed(lines)

    def _set_geom(self):
        self._ctrl_points = []  # none of these to draw
        window_height = .7
        window_width = 0.9
        title_bar_thickness = .05
        x_margin = 0.12
        v_pad = (1 - window_height) / 2
        h_pad = (1 - window_width) / 2
        window_polyline = [[h_pad, 1.0 - v_pad],
                           [1.0-h_pad, 1.0 - v_pad],
                           [1.0-h_pad, v_pad],
                           [h_pad, v_pad],
                           [h_pad, 1.0 - v_pad]]
        title_bar_polyline = [[h_pad, v_pad+title_bar_thickness],
                              [1.0-h_pad,  v_pad+title_bar_thickness]]

        x_left, x_right = h_pad + x_margin, 1.0 - h_pad - x_margin
        x_top, x_bottom = v_pad + title_bar_thickness + x_margin, 1.0 - v_pad - x_margin
        x_lines = [self._correct_lines([(x_left, x_top), (x_right, x_bottom)]),
                   self._correct_lines([(x_right, x_top), (x_left, x_bottom)])]
        window_lines = [self._correct_lines(window_polyline), self._correct_lines(title_bar_polyline)]+x_lines
        self._heavy_lines = window_lines


class UndoRedoIcon(IconArtist):
    # left, right arrows
    def __init__(self, bbox, direction=1, margin_frac=None):
        """
        :param direction: int, 1 for redo, -1 for undo
        """
        self._direction = direction
        super().__init__(bbox, margin_frac, draw_filled=True, closed=True)

    def _set_geom(self):
        arrow_rel = [(0.0, 0.5),  # tip
                     (0.333, 0.2),  # upper corner
                     (0.333, 0.4),  # upper stem corner
                     (.9, 0.4),  # upper stem end
                     (.9, 0.6),  # lower stem end
                     (0.333, 0.6),  # lower stem corner
                     (0.333, 0.8)]
        arrow_rel = np.array(arrow_rel, dtype=np.float64)
        arrow_rel[:, 0] += .05
        if self._direction == -1:
            arrow_rel[:, 0] = 1.0 - arrow_rel[:, 0]
        arrow = scale_points_to_bbox(np.array(arrow_rel, dtype=np.float64), self._bbox, margin_frac=self._margin_frac)
        self._lines = [floats_to_fixed(arrow)]

    def render(self, img, held=False, moused_over=False):
        self.color_v = self._obj_color_v  # don't change color
        super().render(img)


class UndoIcon(UndoRedoIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, direction=1, margin_frac=margin_frac)


class RedoIcon(UndoRedoIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, direction=-1, margin_frac=margin_frac)


class LineToolIcon(IconArtist):
    """
    Draw a line scaled to a smaller square within the unit square (i.e. for the margin)
    show control points at each end
    """

    def _set_geom(self):
        line_coords_rel = np.array([(0.2, 0), (0.6, 1)])
        line_coords = scale_points_to_bbox(line_coords_rel, self._bbox, margin_frac=self._margin_frac)
        self._lines = [floats_to_fixed(line_coords)]

        self._ctrl_points = [line_coords[0], line_coords[1]]


class RectangleToolIcon(CircleToolIcon):
    """
    Draw a rectangle in the bbox , with control points at opposite corners.
    """

    def _set_geom(self):
        corners = [(0, 0), (1, 0), (1, 1), (0, 1)]
        corner_points = scale_points_to_bbox(np.array(corners, dtype=np.float64),
                                             self._bbox, margin_frac=self._margin_frac)

        self._lines = [floats_to_fixed(corner_points)]
        self._ctrl_points = [corner_points[0], corner_points[2]]


class PencilToolIcon(CircleToolIcon):
    """
    Load the "scribble" coordinates, scale to unit square, and draw the scribble.
    The control points are the first and last points.
    """

    def _set_geom(self):
        # scale to unit square

        points = UNIT_SCRIBBLE_COORDS
        points = scale_points_to_bbox(points, self._bbox, margin_frac=self._margin_frac)
        self._lines = [floats_to_fixed(points)]
        self._ctrl_point1 = points[0]
        self._ctrl_point2 = points[-1]

    def render(self, img, held=False, moused_over=False):
        cv2.polylines(img, self._lines, False,
                      self.color_v, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        self._draw_ctrl_point(img, self._ctrl_point1)
        self._draw_ctrl_point(img, self._ctrl_point2)


class PanToolIcon(IconArtist):
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

        self._lines = [floats_to_fixed(scale_points_to_bbox(np.array(rel_line),
                                                            self._bbox,
                                                            margin_frac=self._margin_frac))
                       for rel_line in rel_lines]

        self._ctrl_points = [(x_center, y_center)]

    def render(self, img, held=False, moused_over=False):
        self.color_v = self._obj_color_v
        super().render(img)


class SelectToolIcon(RectangleToolIcon):
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
        lines = top_segments + left_segments + right_segments + bottom_segments
        self._lines = [np.array(line, dtype=np.int32) for line in lines]
        fixed_ctrl_points = [top_segments[0][0], bottom_segments[-1][1]]
        # these are not stored as fixed-point numbers, make them floats again:
        self._ctrl_points = [(x/PREC_SCALE, y/PREC_SCALE) for x, y in fixed_ctrl_points]

    def render(self, img, held=False, moused_over=False):
        self.color_v = self._obj_color_v
        super().render(img)


class LineThicknessIcon(IconArtist):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, margin_frac, draw_filled=True)

    def _set_geom(self):
        """
        Show N horizontal lines of increasing thickness.
        (render as N rectangles)
        """
        n = 4
        line_vol = 0.4  # fraction of the bbox height taken up by the lines (i.e. not background)
        line_thicknesses = np.arange(1, n+1)
        line_thicknesses = line_thicknesses / np.sum(line_thicknesses) * line_vol
        spacing = (1 - line_vol) / (n-1)
        lines = []
        y = [0.]

        def _get_rect_points(i):
            y_bottom, y_top = y[0], y[0]+line_thicknesses[i]
            rect = np.array([(0, y_bottom), (1, y_bottom), (1, y_top), (0, y_top), (0, y_bottom)])
            y[0] = y_top + spacing
            return np.array(rect)

        for i, thickness in enumerate(line_thicknesses):
            lines.append(_get_rect_points(i))
        lines = [scale_points_to_bbox(line, self._bbox, margin_frac=self._margin_frac) for line in lines]
        self._lines = [floats_to_fixed(line) for line in lines]


class TextToolIcon(IconArtist):
    # import from line tool

    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, margin_frac, draw_filled=False, closed=False)

    def _set_geom(self):
        l_width = 0.45
        cap_height = 0.55
        miniscule_size = 0.3
        bottom = cap_height * .3
        cursor = get_text_cursor_points(tail_scale=.3)
        kern = 0.03

        x = np.max(cursor[0][:, 0]) + .2

        t_mid_x = x + l_width/2.
        T_lines = [((t_mid_x, 1.0 - bottom), (t_mid_x, 1.0 - bottom-cap_height)),
                   ((t_mid_x - l_width/2., 1.0 - bottom - cap_height), (t_mid_x + l_width/2., 1.0 - bottom - cap_height)),]
        x += l_width - kern
        x_lines = [((x, 1.0 - bottom), (x + miniscule_size, 1.0 - bottom - miniscule_size)),
                   ((x+miniscule_size, 1.0 - bottom), (x, 1.0 - bottom - miniscule_size))]
        letter_lines = T_lines + x_lines
        self._cursor_lines = [floats_to_fixed(scale_points_to_bbox(
            line, self._bbox, margin_frac=self._margin_frac)) for line in cursor]
        self._text_lines = [floats_to_fixed(scale_points_to_bbox(
            line, self._bbox, margin_frac=self._margin_frac)) for line in letter_lines]

    def render(self, img, held=False, moused_over=False):
        cv2.polylines(img, self._cursor_lines, False, self._faint_color_v,
                      lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)
        cv2.polylines(img, self._text_lines, False, self.color_v, lineType=cv2.LINE_AA, thickness=1, shift=PREC_BITS)


class TextSizeIcon(SnapToGridIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, margin_frac)

    def _make_a(self, size):
        """
        :param size: float [0, 1], 1 is full height (biggest possible in unit square)
        :returns: list of lines ((x1, y1), (x2, y2)) to draw the letter A, bottom left corner at (0, 0)
        """
        aspect = 0.63
        bottom = 1.0
        midline = 0.4  # fraction of the way up the letter A the horizontal line is
        top = bottom - size
        width = size * aspect
        midy, midx = top * midline + bottom * (1.0 - midline), width / 2
        a_lines = [((0, bottom), (midx, top)),
                   ((width, bottom), (midx, top)),
                   ((midx-width/4, midy), (midx+width/4, midy))]
        return np.array(a_lines)

    def _set_geom(self):
        """
        Big A next to a smaller A.
        """
        big_a = self._make_a(0.85)
        small_a = self._make_a(0.35)
        translate_lines(big_a, 0.5, 0.0)
        big_a = [scale_points_to_bbox(line, self._bbox, margin_frac=self._margin_frac) for line in big_a]
        small_a = [scale_points_to_bbox(line, self._bbox, margin_frac=self._margin_frac) for line in small_a]
        self._heavy_lines = [floats_to_fixed(line) for line in big_a + small_a]


class PlaceholderIcon(IconArtist):
    """
    Write a small amount of text instead of drawing something.
    """

    def __init__(self, bbox, text, color=None, margin_frac=None):
        self._font = cv2.FONT_HERSHEY_SIMPLEX
        self._thickness = 1
        self._mouseover_color_v = COLORS_BGR['neon green']
        self._hold_color_v = COLORS_BGR['black']

        self._text = text
        super().__init__(bbox, margin_frac)

    def _set_geom(self):
        # determine text scaling so text fits within margin of bbox
        (width, height), baseline = cv2.getTextSize(self._text, self._font, 1, self._thickness)
        x_min, x_max = self._bbox['x'][0], self._bbox['x'][1]
        y_min, y_max = self._bbox['y'][0], self._bbox['y'][1]
        x_margin = (x_max - x_min) * self._margin_frac/2
        y_margin = (y_max - y_min) * self._margin_frac/2

        self._scale = min((x_max - x_min - 2 * x_margin) / width,
                            (y_max - y_min - 2 * y_margin) / height)
        self._txt_pos = ((x_max + x_min)/2 - width * self._scale/2,
                          (y_max + y_min)/2 + height * self._scale/2)
        
        if isinstance(self, EraseIcon):
            print("Erase bbox:", self._bbox) 

    def render(self, img, held=False, moused_over=False):
        """
        Draw the bbox in obj_color, and the optional mouse boxes.
        Write the text.
        """
        thickness = 1
        if moused_over:
            color = self._mouseover_color_v
        elif held:
            color = self._hold_color_v
            thickness = 2
        else:
            color = self._obj_color_v

        cv2.rectangle(img, (self._bbox['x'][0], self._bbox['y'][0]),
                      (self._bbox['x'][1], self._bbox['y'][1]), color, thickness)

        cv2.putText(img, self._text, (int(self._txt_pos[0]), int(self._txt_pos[1])),
                    self._font, self._scale, color, self._thickness, cv2.LINE_AA)


class EraseIcon(PlaceholderIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, 'erase', margin_frac=margin_frac)


class MoveIcon(PlaceholderIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, 'move', margin_frac=margin_frac)


class ResizeIcon(PlaceholderIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, 'resize', margin_frac=margin_frac)


class RotateIcon(PlaceholderIcon):
    def __init__(self, bbox, margin_frac=None):
        super().__init__(bbox, 'rotate', margin_frac=margin_frac)


# keys should match ToolManager._TOOLS.keys() so buttons can see both.
BUTTON_ARTISTS = {'circle': CircleToolIcon,
                  'rectangle': RectangleToolIcon,
                  'line': LineToolIcon,
                  'pencil': PencilToolIcon,
                  'pan': PanToolIcon,
                  'select': SelectToolIcon,
                  'grid': GridIcon,
                  'undo': UndoIcon,
                  'redo': RedoIcon,
                  'snap_to_grid': SnapToGridIcon,
                  'clear': ClearIcon,
                  'thickness': LineThicknessIcon,
                  'text': TextToolIcon,
                  'text_size': TextSizeIcon,
                    'erase': EraseIcon,
                    'move': MoveIcon,
                    'resize': ResizeIcon,
                    'rotate': RotateIcon,

                  }


_DEFAULT_COLOR_BGR = COLORS_BGR[BOARD_LAYOUT['obj_color']]


def test_icon_artists():
    w = 700
    img1 = np.zeros((200, w, 3), dtype=np.uint8) + np.array(COLORS_BGR['white'], dtype=np.uint8)
    img2 = np.zeros((200, w, 3), dtype=np.uint8) + np.array(COLORS_BGR['white'], dtype=np.uint8)
    margin_frac = 0.3
    spacing = 55
    offset_xy = [10, 10]
    height = 55

    def get_bbox():
        if offset_xy[0] > w - 100:
            offset_xy[0] = 10
            offset_xy[1] += height
        x = offset_xy[0]
        offset_xy[0] += spacing
        y = offset_xy[1]
        print(x, y)
        return {'x': (x, x + spacing), 'y': (y, y+height)}

    icons = {'circle': CircleToolIcon(get_bbox(), margin_frac=margin_frac),
             'line': LineToolIcon(get_bbox(), margin_frac=margin_frac),
             'pencil': PencilToolIcon(get_bbox(), margin_frac=margin_frac),
             'rectangle': RectangleToolIcon(get_bbox(), margin_frac=margin_frac),
             'pan': PanToolIcon(get_bbox(), margin_frac=margin_frac),
             'select': SelectToolIcon(get_bbox(), margin_frac=margin_frac),
             'grid': GridIcon(get_bbox(), margin_frac=margin_frac),
             'undo': UndoIcon(get_bbox(), margin_frac=margin_frac),
             'redo': RedoIcon(get_bbox(), margin_frac=margin_frac),
             'snap_to_grid': SnapToGridIcon(get_bbox(), margin_frac=margin_frac),
             'clear': ClearIcon(get_bbox(), margin_frac=margin_frac),
             'thickness': LineThicknessIcon(get_bbox(), margin_frac=margin_frac),
             'text': TextToolIcon(get_bbox(), margin_frac=margin_frac),
             'text_size': TextSizeIcon(get_bbox(), margin_frac=margin_frac),
                'erase': EraseIcon(get_bbox(), margin_frac=margin_frac),
                'move': MoveIcon(get_bbox(), margin_frac=margin_frac),
                'resize': ResizeIcon(get_bbox(), margin_frac=margin_frac),
                'rotate': RotateIcon(get_bbox(), margin_frac=margin_frac),

             }

    for icon_n in icons:
        # if icon_n=='text_size':
        #    import ipdb; ipdb.set_trace()
        icons[icon_n].boxed_render(img1)

    # Change colors
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple',
              'black', 'black', 'black', 'black', 'neon green', 'black', 'blue', 'green']
    
    if len(colors) < len(icons):
        colors += ['black'] * (len(icons) - len(colors))

    for i, icon_n in enumerate(icons):
        print(icon_n)
        icons[icon_n].color_v = COLORS_BGR[colors[i]]
        icons[icon_n].render(img2)

    img = np.concatenate((img1, img2), axis=0)
    # cv2.imwrite('icon_artists.png', img)
    cv2.imshow('circle', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    test_icon_artists()
