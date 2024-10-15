import cv2
import numpy as np


def get_font_size(bbox, orientation):
    """
    Return a good fontScale and thickness for cv2.putText based on the size of the bounding box.
    """
    return .5, 1
    if orientation == 'horizontal':
        resolution = bbox['x'][1] - bbox['x'][0]
    else:
        resolution = bbox['y'][1] - bbox['y'][0]

    if resolution < 500:
        font_scale = 0.5
        thickness = 1
    elif resolution < 1000:
        font_scale = 1
        thickness = 2
    elif resolution < 2000:
        font_scale = 2
        thickness = 3
    else:
        font_scale = 3
        thickness = 4
    return font_scale, thickness


def is_numeric(items):
    """
    Return True if everything can be cast to a float.
    """
    try:
        for item in items:
            float(item)
    except ValueError:
        return False
    return True


def draw_bbox(img, bbox, color, thickness):
    """
    Draw a rectangle
    :param img: image to draw on
    :param bbox: {x:(x_min, x_max), y:(y_min, y_max)}
    :param color: (r, g, b)
    :param thickness: int, thickness of the line or -1 (cv2.FILLED)
    """
    x_min, x_max = bbox['x']
    y_min, y_max = bbox['y']
    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, thickness)


def get_bbox(points):
    """
    Return a bounding box around the points.
    :param points: Nx2 array
    :return: {x:(x_min, x_max), y:(y_min, y_max)}
    """
    points = np.array(points).reshape(-1, 2)
    return {'x': [np.min(points[:, 0]), np.max(points[:, 1])],
            'y': [np.min(points[:, 1]), np.max(points[:, 1])]}


def in_bbox(bbox, xy_px):
    """
    Return True if xy_px is in the bounding box of the component.
    """
    x, y = xy_px
    return bbox['x'][0] <= x <= bbox['x'][1] and bbox['y'][0] <= y <= bbox['y'][1]


def bboxes_intersect(bbox1, bbox2):
    def intervals_overlap(int1, int2):
        return int1[0] <= int2[1] and int2[0] <= int1[1]
    x_overlaps = intervals_overlap(bbox1['x'], bbox2['x'])
    y_overlaps = intervals_overlap(bbox1['y'], bbox2['y'])
    return x_overlaps and y_overlaps


def get_circle_points(center, radius, num_points=100):
    """
    Return a numpy array of points in a circle.
    """
    theta = np.linspace(0, 2 * np.pi, num_points)
    x = center[0] + radius * np.cos(theta)
    y = center[1] + radius * np.sin(theta)
    return np.array([x, y]).T

PREC_BITS = 7  # number of bits to use for precision in fixed-point numbers
PREC_SCALE = 2 ** PREC_BITS  # for cv2 draw commands
def floats_to_fixed(points):
    """
    Convert an array of floats to fixed-point numbers.
    (call before plotting with cv2 using argument shift=PREC_BITS)
    """
    return np.round(points * PREC_SCALE).astype(np.int32)


def scale_points_to_bbox(unit_points, bbox, margin_frac=0.0):
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
    return np.array([(x_min + x * x_scale,
                                      y_min + y * y_scale)
                                     for x, y in unit_points])