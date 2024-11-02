import json
from vectors import Vector, PencilVec, LineVec, CircleVec, RectangleVec
import numpy as np
from layout import EMPTY_BBOX
import logging
from util import in_bbox

VECTORS = [PencilVec, LineVec, CircleVec, RectangleVec]


class VectorManager(object):
    """
    Manages set of vectors on the board.
    """

    def __init__(self, load_file=None):
        if load_file:
            self.load(load_file)
        self._vectors = []
        self._deleted = []  # list of deleted vectors (current stored in self._vectors)
        self._types = {cls.__name__: cls for cls in VECTORS}


    def save(self, filename):

        def _serialize(vector):
            packet = {'class': vector.name,  # vector names are their separate class names.
                      'data': vector.get_data()}
            return json.dumps(packet)

        vectors = [_serialize(vector) for vector in self._vectors]
        deleted = [_serialize(vector) for vector in self._deleted]


        with open(filename, 'w') as f:
            json.dump([vectors, deleted], f)

    def load(self, filename):

        def _deserialize(string):
            packet = json.loads(string)
            return self._types[packet['class']].from_data(packet['data'])

        with open(filename, 'r') as f:
            vectors, deleted = json.load(f)

        self._vectors = [_deserialize(vector) for vector in vectors]
        self._deleted =[_deserialize(vector) for vector in deleted]


    def get_vectors_in(self, bbox):
        """
        Return all vectors that are visible in the bbox.
        i.e. whose bboxes intersect the given bbox.
        """
        return [vector for vector in self._vectors if vector.inside(bbox)]

    def add_vector(self, vector):
        self._vectors.append(vector)

    def delete(self, vector):
        self._deleted.append(vector)
        self._vectors.remove(vector)

    def undo_delete(self):
        if self._deleted:
            self._vectors.append(self._deleted.pop())

    def render(self, img, view):
        #print("Rendering %i vectors" % len(self._vectors))
        for vector in self._vectors:
            vector.render(img, view)

    def mouse_event(self, event, x, y, flags, param):
        # vectors are not interactive, only controlled by tools & controls.
        pass
