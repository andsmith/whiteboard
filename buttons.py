
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox
from gui_components import UIElement, MouseReturnStates
from controls import Control
import logging

class Button(Control):
    """
    A button that can be clicked.
    """

    def __init__(self, canvas, name, bbox, visible=True, init_state=False, callbacks=(), pinned=True):
        """
        :param init_state: bool, initial state of the button
        :param callbacks: list of functions to be called when the button is clicked, 
            with args=(self, state)
        """
        super().__init__(canvas, name, bbox, visible, pinned)
        logging.info("Created Button %s" % name)
        self.state = init_state
        self.moused_over = False
        self.callbacks = list(callbacks)

    def _change_state(self):
        self.state = not self.state
        for callback in self.callbacks:
            callback(self.name, self.state)

    def mouse_event(self, event, x, y, flags, param):
        if self.in_bbox((x, y)):
            self.moused_over = True
            if event == cv2.EVENT_LBUTTONDOWN:
                return self._capture_mouse()
            elif event == cv2.EVENT_LBUTTONUP:
                self._change_state()
                return self._release_mouse()
            return MouseReturnStates.captured if self._has_mouse else MouseReturnStates.released
        else:
            self.moused_over = False
            if self._has_mouse and event == cv2.EVENT_LBUTTONUP:
                return self._release_mouse()
            return MouseReturnStates.captured if self._has_mouse else MouseReturnStates.unused

    def render(self, img, box_color=(255, 255, 255), show_bbox=True):
        # Subclasses do something fancier, this is just a box and a label.
        print("%s is moused over: %s" % (self.name, self.moused_over))
        if self._visible:
            p1 = (self._bbox['x'][0], self._bbox['y'][0])
            p2 = (self._bbox['x'][1], self._bbox['y'][1])
            if show_bbox:
                cv2.rectangle(img, p1, p2, box_color, 1 if not self.moused_over else 4)
            label = '{}={}'.format(self.name, 'ON' if self.state else 'OFF')
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

    def __init__(self, canvas, name, bbox, button_grid, exclusive=False, visible=True, pinned=True):
        """
        (ignores button's individual bboxes, aranges according to bbox & button_grid)
        :param exclusive: if True, treated as radio buttons, else as checkboxes
        :param button_grid: list of lists of Button objects (can be None), 
            to be displayed in that arangement, in the bbox.
        """
        super().__init__(canvas, name, bbox, visible, pinned)
        self._exclusive = exclusive
        self._button_grid = button_grid
        self.buttons = []  # flattened list of buttons

        self._init_geom()
        logging.info("Created ButtonBox %s" % name)

        # set up callbacks so each button turns all the others off.
        for button in self.buttons:
            button.callbacks.append(self._radio_click_callback)

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
                    self.buttons.append(button)

    def move_to(self, x, y, new_bbox=None):
        super().move_to(x, y, new_bbox)
        self._init_geom()

    def _radio_click_callback(self, button, state):
        if state and self._exclusive:
            for other_button in self.buttons:
                if other_button != button:
                    other_button.set_state(False)

    def mouse_event(self, event, x, y, flags, param):
        for button in self.buttons:
            rv = button.mouse_event(event, x, y, flags, param)
            if rv != MouseReturnStates.unused:
                return rv
        return MouseReturnStates.unused
    
    def render(self, img, show_bbox=True):
        for button in self.buttons:
            button.render(img, show_bbox=show_bbox)

        if show_bbox:
            p1 = (self._bbox['x'][0], self._bbox['y'][0])
            p2 = (self._bbox['x'][1], self._bbox['y'][1])

            cv2.rectangle(img, p1, p2, (255, 255, 255), 1)