import cv2
import numpy as np


def corners_from_bbox(bbox):
    """
    :param bbox:  dict(x=(x_min, x_max), y=(y_min, y_max))
    :return: 4x2 array of corner points
    """
    x_min, x_max = bbox['x']
    y_min, y_max = bbox['y']
    return np.array([(x_min, y_min),
                     (x_max, y_min),
                     (x_max, y_max),
                     (x_min, y_max)])


def move_bbox_to(bbox, xy):
    """
    Translate the bbox.
    """
    w, h = bbox['x'][1] - bbox['x'][0], bbox['y'][1] - bbox['y'][0]
    return {'x': (xy[0], xy[0] + w),
            'y': (xy[1], xy[1] + h)}


def unit_to_abs_bbox(unit_bbox, win_size):
    """
    Scale the bounding box within [0,1]x[0,1] to [0, win_size[0]]x[0, win_size[1]]
    """
    x_min, x_max = unit_bbox['x']
    y_min, y_max = unit_bbox['y']
    return {'x': (int(x_min * win_size[0]), int(x_max * win_size[0])),
            'y': (int(y_min * win_size[1]), int(y_max * win_size[1]))}


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


def interp_colors(color1, color2, frac):
    """
    :param color1: (r, g, b)
    :param color2: (r, g, b)
    :param frac: 0-1
    """
    return tuple(int(c1 * (1 - frac) + c2 * frac) for c1, c2 in zip(color1, color2))


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
    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, thickness, lineType=cv2.LINE_AA)


def get_bbox(points):
    """
    Return a bounding box around the points.
    :param points: Nx2 array
    :return: {x:(x_min, x_max), y:(y_min, y_max)}
    """
    points = np.array(points).reshape(-1, 2)
    return {'x': [np.min(points[:, 0]), np.max(points[:, 0])],
            'y': [np.min(points[:, 1]), np.max(points[:, 1])]}


def in_bbox(bbox, xy_px):
    """
    Return True if xy_px is in the bounding box of the component.
    """
    x, y = xy_px
    return bbox['x'][0] <= x <= bbox['x'][1] and bbox['y'][0] <= y <= bbox['y'][1]
def expand_bbox(bbox, xy):
    """
    Expand the bounding box to include the point.
    """
    x, y = xy
    x_min, x_max = bbox['x']
    y_min, y_max = bbox['y']
    return {'x': [min(x_min, x), max(x_max, x)],
            'y': [min(y_min, y), max(y_max, y)]}

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


def get_text_cursor_points( tail_scale=.25, num_points=25):
    """
    Return a classic text cursor shape centered in the unit square.
    :param center: (x, y)
    :param tail_scale: length of curved portions wrt the middle stem.
    """
    height=1.0
    stem_height = height * (1.0 - tail_scale)
    tail_height = height * tail_scale / 2
    circle_points = get_circle_points((0.,0.), tail_height, num_points*4)
    quadrants = {'ur': circle_points[:num_points][::-1],  # reverse to end at the vertical part
                 'ul': circle_points[num_points:2*num_points],
                 'll': circle_points[2*num_points:3*num_points],
                 'lr': circle_points[3*num_points:][::-1]}
    cursor_left = np.vstack((quadrants['ur'] + np.array((-tail_height, stem_height/2)),
                             quadrants['lr'] + np.array((-tail_height, -stem_height/2)) ))
    cursor_right = np.vstack((quadrants['ul'] + np.array((tail_height, stem_height/2)),
                                quadrants['ll'] + np.array((tail_height, -stem_height/2)) ))
    allpts = np.vstack((cursor_left, cursor_right))
    shift = np.min(allpts, axis=0)

    cursor_left -= shift
    cursor_right -= shift
    pts =  [cursor_left, cursor_right]
    return pts


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
    pts = np.array([(x_min + x * x_scale,
                      y_min + y * y_scale)
                     for x, y in unit_points])
    return pts

def test_cursor():
    import matplotlib.pyplot as plt
    cursor_points = get_text_cursor_points()
    for points in cursor_points:
        plt.plot(points[:, 0], points[:, 1])
    plt.gca().set_aspect('equal')
    plt.show()



if __name__=="__main__":
    test_cursor()