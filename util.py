import cv2
import numpy as np


def get_font_size(bbox, orientation):
    """
    Return a good fontScale and thickness for cv2.putText based on the size of the bounding box.
    """
    return .5,1
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



def in_bbox(bbox, xy_px):
    """
    Return True if xy_px is in the bounding box of the component.
    """
    x, y = xy_px
    return bbox['x'][0] <= x <= bbox['x'][1] and bbox['y'][0] <= y <= bbox['y'][1]
