
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox
from gui_components import UIElement, MouseReturnStates


class Control(UIElement):
    """
    Abstract class for all UI components (things you can interact with on the window)
    """

    def __init__(self, canvas, name, bbox, visible=True, pinned=True):
        """
        :param canvas: a Canvas object
        :param bbox: {'x': (x_min, x_max), 'y': (y_min, y_max)}
        :param visible: bool, whether the control is visible initially
        :param pinned: bool, whether the control is pinned to the window (True) or moves/resizes with the canvas (False)
        """
        super().__init__(canvas, name, bbox, visible, pinned)

    def in_bbox(self, xy_px):
        if self._bbox is None:
            return True
        return in_bbox(self._bbox, xy_px)

    def move_to(self, x, y, new_bbox=None):
        if new_bbox is None:
            self._bbox = {'x': (x, x + self._bbox['x'][1] - self._bbox['x'][0]),
                          'y': (y, y + self._bbox['y'][1] - self._bbox['y'][0])}
        else:
            self._bbox = new_bbox

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        :return: MouseReturnStates
        """
        pass

    @abstractmethod
    def render(self, img, show_bbox=True):
        pass


class Button(Control):
    """
    A button that can be clicked.
    """

    def __init__(self, canvas, name, bbox, visible=True, init_state=False, pinned=True):
        super().__init__(canvas, name, bbox, visible, pinned)
        self.state = init_state
        self.moused_over = False

    def is_held(self):
        # clicked but not released
        return self._has_mouse

    def mouse_event(self, event, x, y, flags, param):
        if self.in_bbox((x, y)):
            self.moused_over = True
            if event == cv2.EVENT_LBUTTONDOWN:
                return self._capture_mouse()
            elif event == cv2.EVENT_LBUTTONUP: 
                self.state = not self.state
                return self._release_mouse()
            return MouseReturnStates.captured if self._has_mouse else MouseReturnStates.released
        else:
            self.moused_over = False
            if self._has_mouse and event == cv2.EVENT_LBUTTONUP:
                return self._release_mouse()
            return MouseReturnStates.captured if self._has_mouse else MouseReturnStates.unused

    def render(self, img, box_color=(255, 255, 255), show_bbox=True):
        # Subclasses do something fancier, this is just a box and a label.
        if self._visible:
            p1 = (self._bbox['x'][0], self._bbox['y'][0])
            p2 = (self._bbox['x'][1], self._bbox['y'][1])
            if show_bbox:
                cv2.rectangle(img, p1, p2, box_color, 1 if not self.moused_over else 4)
            label = '{}={}'.format(self._name, 'ON' if self.state else 'OFF')
            cv2.putText(img, label, (self._bbox['x'][0] + 5, self._bbox['y'][0] + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state


class ButtonBox(Control):
    """
    A group of buttons that can be clicked.
    """

    def __init__(self, canvas, bbox, button_grid, exclusive=True, visible=True, pinned=True):
        """
        (ignores button's individual bboxes, aranges according to bbox & button_grid)
        :param exclusive: if True, treated as radio buttons, else as checkboxes
        :param button_grid: list of lists of Button objects (can be None), 
            to be displayed in that arangement, in the bbox.
        """
        super().__init__(canvas, bbox, visible, pinned)
        self._exclusive = exclusive
        self._buttons = []
        self._button_grid = button_grid
        self._init_geom()

    def _init_geom(self):
        x_min, x_max = self._bbox['x']
        y_min, y_max = self._bbox['y']
        n_rows = len(self._button_grid)
        n_cols = max(len(row) for row in self._button_grid)
        w = (x_max - x_min) // n_cols
        h = (y_max - y_min) // n_rows
        for i, row in enumerate(self._button_grid):
            for j, button in enumerate(row):
                if button is not None:
                    button.move_to(0, 0, new_bbox={'x': (x_min + j * w, x_min + (j + 1) * w),
                                                   'y': (y_min + i * h, y_min + (i + 1) * h)})
                    self._buttons.append(button)

    def move_to(self, x, y, new_bbox=None):
        super().move_to(x, y, new_bbox)
        self._init_geom()



    def mouse_event(self, event, x, y, flags, param):
        if self._active_button is not None:
            rv = self._active_button.mouse_event(event, x, y, flags, param)
            if rv == MouseReturnStates.released:
                self._active_button = None
            return MouseReturnStates.captured
        else:
            for button in self._buttons:
                rv = button.mouse_event(event, x, y, flags, param)
                if rv == MouseReturnStates.captured:
                    self._active_button = button
                    return MouseReturnStates.captured
        return MouseReturnStates.released
