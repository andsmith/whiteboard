import json
from vectors import Vector, PencilVec, LineVec, CircleVec, RectangleVec
from gui_components import UIManager
import numpy as np
from layout import EMPTY_BBOX
import logging
from util import in_bbox
from abc import ABC, abstractmethod

VECTORS = [PencilVec, LineVec, CircleVec, RectangleVec]


class VectorManager(UIManager):
    """
    Manages set of vectors on the board.
    """

    def __init__(self, board, load_file=None):
        self._board = board
        if load_file:
            self.load(load_file)
        self._deleted = []  # list of deleted vectors (current stored in self._elements)
        super().__init__(board, 'Vector Manager', EMPTY_BBOX, visible=False)
        self._types = {cls.__name__: cls for cls in VECTORS}

    def _init_elements(self):
        pass  # init was done by the load, if necessary.

    def save(self, filename):

        def _serialize(vector):
            packet = {'class': vector.name,  # vector names are their separate class names.
                      'data': vector.get_data()}
            return json.dumps(packet)

        vectors = [_serialize(vector) for vector in self._elements]
        deleted = [_serialize(vector) for vector in self._deleted]


        with open(filename, 'w') as f:
            json.dump([vectors, deleted], f)

    def load(self, filename):

        def _deserialize(string):
            packet = json.loads(string)
            return self._types[packet['class']].from_data(packet['data'])

        with open(filename, 'r') as f:
            vectors, deleted = json.load(f)

        self._elements = [_deserialize(vector) for vector in vectors]
        self._deleted =[_deserialize(vector) for vector in deleted]


    def get_vectors_in(self, bbox):
        """
        Return all vectors that are visible in the bbox.
        i.e. whose bboxes intersect the given bbox.
        """
        return [vector for vector in self._elements if vector.inside(bbox)]

    def add_vector(self, vector):
        self._elements.append(vector)

    def delete(self, vector):
        self._deleted.append(vector)
        self._elements.remove(vector)

    def undo_delete(self):
        if self._deleted:
            self._elements.append(self._deleted.pop())

    def render(self, img, view):
        print("Rendering %i vectors" % len(self._elements))
        for vector in self._elements:
            print(vector.name, vector._color, vector._thickness)
            vector.render(img, view)

    def mouse_event(self, event, x, y, flags, param):
        # vectors are not interactive, only controlled by tools & controls.
        pass
