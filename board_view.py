"""
Define some lightweight UI elements for the app.
"""
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
import logging
from enum import IntEnum
from util import in_bbox, bboxes_intersect


class BoardView(object):
    """
    Represents the view of some part of the board (the cartesian plane) associated
    with a window that renders part of it.  (controls/tools render differently depending on the view.)
    """

    def __init__(self, win_name, size, origin, zoom):
        self.origin = origin  # upper left pixel in the view has this position in the board.
        self.zoom = zoom  # pixels per board unit
        self.size = size  # size of the view in pixels (w x h)
        self.win_name = win_name  # name of the window that renders this view.

        # bounding box of this view within the board, in board coords.
        self.board_bbox = {'x': (origin[0], origin[0] + size[0] / zoom),
                           'y': (origin[1], origin[1] + size[1] / zoom)}

    def __hash__(self) -> int:
        return hash((self.origin, self.zoom, self.size))

    def pan(self, delta_xy):
        """
        :param delta_xy: (dx, dy) in pixels
        """
        origin = self.origin - np.array(delta_xy) / self.zoom
        return BoardView(self.win_name, self.size, origin, self.zoom)

    def from_new_size(self, new_size):
        """
        Create a new view with the new window size.
        When the aspect ratio changes, pick zoom level that inscribes the old view and is centered.
        """
        x_range = self.board_bbox['x'][1] - self.board_bbox['x'][0]
        y_range = self.board_bbox['y'][1] - self.board_bbox['y'][0]
        aspect = x_range / y_range
        new_aspect = new_size[0] / new_size[1]
        if new_aspect > aspect:
            # new window is wider, use height to determine zoom
            zoom = new_size[1] / y_range
            x_center = (self.board_bbox['x'][0] + self.board_bbox['x'][1]) / 2
            x_range = new_size[0] / zoom
            origin = (x_center - x_range / 2, self.board_bbox['y'][0])
        else:
            # new window is taller, use width to determine zoom
            zoom = new_size[0] / x_range
            y_center = (self.board_bbox['y'][0] + self.board_bbox['y'][1]) / 2
            y_range = new_size[1] / zoom
            origin = (self.board_bbox['x'][0], y_center - y_range / 2)
        return BoardView(self.win_name, new_size, origin, zoom)

    def pts_from_pixels(self, xy):
        xy = np.array(xy)
        return (xy / self.zoom) + self.origin

    def pts_to_pixels(self, xy):
        # flip y?
        xy = np.array(xy)
        return (xy - self.origin) * self.zoom

    def sees_bbox(self, bbox):
        """
        Returns True if the view sees any part of the bbox.
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)} in board coords.
        """
        return bboxes_intersect(self.board_bbox, bbox)


def get_board_view(name, points, win_size, margin=0.05):
    """
    Return a BoardView object that cointains all the points centered in it w/a margin.
    """
    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    # Determine if vertical hor horizontal padding is needed (beyond the margin).
    data_aspect = (x_max - x_min) / (y_max - y_min)
    view_aspect = win_size[0] / win_size[1]
    if data_aspect > view_aspect:
        # data is wider than view, add vertical padding
        y_range = (x_max - x_min) / view_aspect
        y_center = (y_max + y_min) / 2
        y_min = y_center - y_range / 2
        y_max = y_center + y_range / 2
    else:
        # data is taller than view, add horizontal padding
        x_range = (y_max - y_min) * view_aspect
        x_center = (x_max + x_min) / 2
        x_min = x_center - x_range / 2
        x_max = x_center + x_range / 2

    x_range = x_max - x_min
    y_range = y_max - y_min
    x_margin = x_range * margin
    y_margin = y_range * margin
    origin = (x_min - x_margin, y_min - y_margin)
    size = (x_range + 2 * x_margin, y_range + 2 * y_margin)
    zoom = min(win_size[0] / size[0], win_size[1] / size[1])
    return BoardView(name, win_size, origin, zoom)
