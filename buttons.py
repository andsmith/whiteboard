
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
    A button that can be moused over & clicked.  Clicks can trigger callbacks and/or change state.
    """

    def __init__(self, board, name, bbox, states=(False, True), callbacks=(), action_mouseup=True, pinned=False):
        """
        #TODO: Fix callback semantics for radio buttons (on state change, not on activate only?)
        :param states: list of states to cycle through (add a callback if this needs changing)
        :param callbacks: list of functions to call when the button is clicked, after the new
            state is set. i.e.:

                def click():
                    ...
                    self.state = new_state
                    [callback(self, new_state, old_state) for callback in self.callbacks]

        :param action_mouseup: if True, the button changes state on mouseup, else on mousedown.
        :param pinned: if True, the button moves with the board, else it is fixed WRT the window.
        """
        super().__init__(board, name, bbox, True, pinned)
        logging.info("Created Button %s" % name)
        self._states = states
        self.state = states[0]
        self.moused_over = False
        self.callbacks = list(callbacks)
        self.action_mouseup = action_mouseup

    def _activate(self):
        """
        Change state and call callbacks.
        """
        print("Activating %s" % self.name)
        old_state = self.state
        self.state = self._states[(self._states.index(self.state) + 1) % len(self._states)]
        for callback in self.callbacks:
            callback(self, self.state, old_state)

    def mouse_event(self, event, x, y, flags, param):
        if self.in_bbox((x, y)):
            self.moused_over = True
            if event == cv2.EVENT_LBUTTONDOWN:
                if not self.action_mouseup:
                    self._activate()
                    return self._release_mouse()
                return self._capture_mouse()
            elif event == cv2.EVENT_LBUTTONUP:
                if not self._has_mouse:
                    return MouseReturnStates.unused
                if self.action_mouseup:
                    self._activate()
                return self._release_mouse()
            return MouseReturnStates.captured if self._has_mouse else MouseReturnStates.released
        else:
            self.moused_over = False
            if self._has_mouse and event == cv2.EVENT_LBUTTONUP:
                return self._release_mouse()
            return MouseReturnStates.captured if self._has_mouse else MouseReturnStates.unused

    def render(self, img, box_color=(255, 255, 255), show_bbox=True):
        # Subclasses do something fancier, this is just a box and a label.
        thickness = 1
        if self.moused_over:
            thickness += 2
        if self._has_mouse:
            thickness += 5

        if self.visible:
            p1 = (self._bbox['x'][0], self._bbox['y'][0])
            p2 = (self._bbox['x'][1], self._bbox['y'][1])
            if show_bbox:
                cv2.rectangle(img, p1, p2, box_color, thickness)
            label = '{}={}'.format(self.name, 'ON' if self.state else 'OFF')
            cv2.putText(img, label, (self._bbox['x'][0] + 5, self._bbox['y'][0] + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1, lineType=cv2.LINE_AA)

    def get_state(self):
        return self.state
    def get_states(self):
        return self._states

    def set_state(self, state):
        # does not trigger callbacks!
        self.state = state


class ButtonBox(Control):
    """
    A group of buttons that can be clicked.
    """

    def __init__(self, board, name, bbox, button_grid,exclusive=False,
                  exclusive_init=None, visible=True, pinned=True):
        """
        (ignores button's individual bboxes, aranges according to bbox & button_grid)
        :param exclusive: if True, only one button can be true at a time.
            Exclusive means only one can be true at a time.  For all buttons in such a ButtonBox:
              * states must be (True, False),
              * state can be set True by clicking, but can only be set to False by clicking on another button.
              * each button gets an extra callback to enforce these conditions when it's activated.
        :param exclusive_init: if Not None, should point to one of the buttons in button_grid, indicating which starts as True.
        :param button_grid: list of lists of Button objects (can be None), 
            to be displayed in that arangement, in the bbox.
        """
        super().__init__(board, name, bbox, visible, pinned)
        self._exclusive = exclusive
        self._button_grid = button_grid
        self.buttons = []  # flattened list of buttons
        self._down_ind = None

        self._init_geom()
        self._init_semantics(exclusive_init)

        logging.info("Created ButtonBox %s (Exclusive=%s)" % (name, exclusive))

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

    def _init_semantics(self, init_on_button):
        # nothing to do for regular button boxes?

        if self._exclusive:
            # check all buttons are true/false:
            for button in self.buttons:
                if set(button.get_states())!=set((True, False)):
                    raise ValueError("Radio Buttons must have states=(true,false).")
                print("Adding callback to %s" % button.name)
                button.callbacks.append(self._radio_click_callback)
                button.exclusive = True
                button.action_mouseup = False
                if init_on_button is not None:
                    if button is init_on_button:
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
        print("Callback for %s (%s, %s)" % (button.name, new_state, old_state))
        if new_state:
            for other_button in self.buttons:
                if other_button is not button:
                    other_button.set_state(False)
        else:       
            button.set_state(True)
            print("Fixed state of %s" % button.name)

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

    def render(self, img, show_bbox=True):
        for button in self.buttons:
            button.render(img, show_bbox=show_bbox)

        if show_bbox:
            p1 = (self._bbox['x'][0], self._bbox['y'][0])
            p2 = (self._bbox['x'][1], self._bbox['y'][1])

            cv2.rectangle(img, p1, p2, (255, 255, 255), 1)
