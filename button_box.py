
import numpy as np
import cv2
from util import in_bbox
from gui_components import MouseReturnStates
from controls import Control
import logging


class ButtonBox(Control):
    """
    A group of buttons that can be clicked.
    """

    def __init__(self, window, name, bbox, button_grid, exclusive=False,
                 exclusive_init=None, visible=True):
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
        self._exclusive = exclusive
        self._button_grid = button_grid
        self.buttons = []  # flattened list of buttons
        self._down_ind = None
        self._over_ind = None
        super().__init__(window, name, bbox, visible)
        self._init_semantics(exclusive_init)
        logging.info("Created ButtonBox %s (Exclusive=%s)" % (name, exclusive))

    def render(self, img, show_bbox=True):
        if self.visible:
            for button in self.buttons:
                button.render(img, show_bbox)
            if show_bbox:
                cv2.rectangle(img, (self._bbox['x'][0], self._bbox['y'][0]),
                              (self._bbox['x'][1], self._bbox['y'][1]),
                              (255, 255, 255), 1)

    def _set_geom(self):
        # Determine grid layout
        x_min, x_max = self._bbox['x']
        y_min, y_max = self._bbox['y']
        n_rows = len(self._button_grid)
        n_cols = max(len(row) for row in self._button_grid)
        w = (x_max - x_min) // n_cols
        h = (y_max - y_min) // n_rows
        # move buttons:
        for i, row in enumerate(self._button_grid):
            for j, button in enumerate(row):
                if button is not None:
                    button.move_to((0, 0), new_bbox={'x': (x_min + j * w, x_min + (j + 1) * w),
                                                     'y': (y_min + i * h, y_min + (i + 1) * h)})
                    self.buttons.append(button)

    def _find_button(self, xy):
        for i, button in enumerate(self.buttons):
            if button.in_bbox(xy):
                return i
        return None

    def _init_semantics(self, init_on_button):
        if self._exclusive:

            init_set_state = init_on_button if init_on_button is not None else self.buttons[0]

            for button in self.buttons:
                # check all buttons are true/false:
                if set(button.get_states()) != set((True, False)):
                    raise ValueError("Radio Buttons must have states=(true,false).")

                # add callback & set flags to enforce radio-button semantics
                button._callbacks.append(self._radio_click_callback)
                button._exclusive = True
                button._action_mouseup = False

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

    def _update_mouseovers(self, xy):
        # Mouse moved, see if we're over a (new) button.
        new_over_ind = self._find_button(xy)
        if new_over_ind is not None:
            if self._over_ind is not None:
                self.buttons[self._over_ind].mouse_out(xy, self.name)
            self.buttons[new_over_ind].mouse_over(xy, self.name)
            self._over_ind = new_over_ind
        elif self._over_ind is not None:
            self.buttons[self._over_ind].mouse_out(xy, self.name)
            self._over_ind = None

    def mouse_down(self, xy):
        """
        Clicked somwehere in our bbox.
        """
        button = self._find_button(xy)
        if button is not None:
            rv = self.buttons[button].mouse_down(xy)
            if rv == MouseReturnStates.captured:
                self._down_ind = button
            return rv
        return MouseReturnStates.unused

    def mouse_up(self, xy):
        """
        Released mouse button.
        """
        if self._down_ind is not None:
            rv = self.buttons[self._down_ind].mouse_up(xy)
            self._down_ind = None
            return rv
        return MouseReturnStates.unused

    def mouse_move(self, xy):
        """
        Mouse moved.
        """
        self._update_mouseovers(xy)
        if self._down_ind is not None:
            return self.buttons[self._down_ind].mouse_move(xy)
        return MouseReturnStates.unused

    def mouse_out(self, xy):
        pass

    def mouse_over(self, xy):
        pass
