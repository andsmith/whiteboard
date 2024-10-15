
import numpy as np
import cv2
from util import in_bbox
from gui_components import UIElement, MouseReturnStates
from controls import Control
import logging


class ButtonBox(Control):
    """
    A group of buttons that can be clicked.
    """

    def __init__(self, board, name, bbox, button_grid, exclusive=False,
                 exclusive_init=None, visible=True, pinned=True):
        """
        (ignores button's individual bboxes, aranges according to bbox & button_grid)
        :param exclusive: if True, only one button can be true at a time.
            Exclusive means only one can be true at a time.  For all buttons in such a ButtonBox:
              * states must be (True, False),
              * state can be set True by clicking, but can only be set to False by clicking on another button.
              * each button gets an extra callback to enforce these conditions when it's activated.
        :param exclusive_init: if Not None, should point to one of the buttons in button_grid, indicating which starts as True.
            otherwise, it is undefined.
        :param button_grid: list of lists of Button objects (can be None), 
            to be displayed in that arangement, in the bbox.
        """
        super().__init__(board, name, bbox, visible, pinned)
        self._exclusive = exclusive
        self._button_grid = button_grid
        self.buttons = []  # flattened list of buttons
        self._down_ind = None

        self._set_geom()

        self._init_semantics(exclusive_init)

        logging.info("Created ButtonBox %s (Exclusive=%s)" % (name, exclusive))

    def _set_geom(self):
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

    def _init_semantics(self, init_on_button):
        if self._exclusive:

            init_set_state = init_on_button if init_on_button is not None else self.buttons[0]
            
            for button in self.buttons:
                # check all buttons are true/false:
                if set(button.get_states()) != set((True, False)):
                    raise ValueError("Radio Buttons must have states=(true,false).")
                # add callback & set flags to enforce radio-button semantics
                button.callbacks.append(self._radio_click_callback)
                button.exclusive = True
                button.action_mouseup = False

                # set the correct initial state
                if button is init_set_state:
                    button.set_state(True)
                else:
                    button.set_state(False)

        else:
            if init_on_button is not None:
                raise ValueError("Non-exclusive button boxes should not have an exclusive_init.")

    def _radio_click_callback(self, button, new_state, old_state):
        """
        (will not be called if self._exclusive is False)

        This is an extra callback added to all buttons if the buttonbox is exclusive, i.e. a radio-button group.
            if new_state is True:
                Set other buttons to False. 
            else:
                set self to True (i.e. don't allow turning off a button, only deactivating it by selecting another).
        """
        if new_state:
            for other_button in self.buttons:
                if other_button is not button:
                    other_button.set_state(False)
        else:
            button.set_state(True)

    def move_to(self, x, y, new_bbox=None):
        super().move_to(x, y, new_bbox)
        self._init_geom()

    def mouse_event(self, event, x, y, flags, param):
        """
        Send all buttons the event so they can change their pressed/moused-over state.
        Remember which button captures the mouse.
        """
        capture_state = MouseReturnStates.unused
        if self._down_ind is not None:  # a button is being pushed, send the signal
            rv = self.buttons[self._down_ind].mouse_event(event, x, y, flags, param)
            if rv == MouseReturnStates.released:
                self._down_ind = None
                return MouseReturnStates.released
        else:
            for i, button in enumerate(self.buttons):
                rv = button.mouse_event(event, x, y, flags, param)
                if rv == MouseReturnStates.captured:
                    self._down_ind = i
                    return MouseReturnStates.captured
                elif rv == MouseReturnStates.released:
                    capture_state = MouseReturnStates.released
        return capture_state

    def render(self, img):
        for button in self.buttons:
            button.render(img)
