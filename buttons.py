
import numpy as np
import cv2
import json
from abc import ABC, abstractmethod
from util import in_bbox, get_circle_points, floats_to_fixed, PREC_BITS
from gui_components import UIElement, MouseReturnStates
from controls import Control
import logging
from layout import COLORS_BGR, COLOR_BUTTONS, BOARD_LAYOUT, TOOL_BUTTONS
from icon_artists import  BUTTON_ARTISTS

class Button(Control):
    """
    A button that can be moused over & clicked.  Clicks can trigger callbacks and/or change state.
    """

    def __init__(self, board, name, bbox, states=(False, True), callbacks=(), action_mouseup=True, pinned=False, show_bbox=True):
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
        self._mouseover_color_v = COLORS_BGR[COLOR_BUTTONS['mouseover_color']]
        self._selected_color_v = COLORS_BGR[COLOR_BUTTONS['selected_color']]
        self._unselected_color_v = None # COLORS_BGR[COLOR_BUTTONS['unselected_color']]
        self._text_color_v = COLORS_BGR[BOARD_LAYOUT['obj_color']]
        
        self._show_bbox = show_bbox

    def _set_geom(self):
        pass  # rendered from bbox directly

    def _activate(self):
        """
        Change state and call callbacks.
        """
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
        
    def _draw_bbox(self, img, color_v,thickness=1):
        p1 = (self._bbox['x'][0], self._bbox['y'][0])
        p2 = (self._bbox['x'][1], self._bbox['y'][1])
        cv2.rectangle(img, p1, p2, color_v, thickness=thickness, lineType=cv2.LINE_AA)

    def render(self, img):
        # Subclasses do something fancier, this is just a box and a label.
        # Show_bbox=true will draw the bounding box of the button, depending on mouseover/button state.
        if self.visible:

            color_v = self._get_state_color()
            if self._show_bbox:
                color_v = color_v if color_v is not None else self._text_color_v  # show anyway 

                thickness=1 if not self.state else 2
                self._draw_bbox(img, color_v, thickness)

            label = '{}={}'.format(self.name,  self.state )
            cv2.putText(img, label, (self._bbox['x'][0] + 5, self._bbox['y'][0] + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, self._text_color_v, 1, lineType=cv2.LINE_AA)
            
    def _get_state_color(self):
        """
        For displaying the state of the button.
        """
        
        c = self._unselected_color_v
        if self.moused_over:
            c = self._mouseover_color_v
        if self.state:
            c = self._selected_color_v
        return c

    def get_state(self):
        return self.state

    def get_states(self):
        return self._states

    def set_state(self, state):
        # does not trigger callbacks!
        self.state = state


class CircleButton(Button, ABC):
    """
    Round button w/an outine indicating mouse state and something drawn in the middle.
    """

    def __init__(self, board, name, bbox, callbacks=(), action_mouseup=True, pinned=False, outline_frac=None):
        """
        :param outline_frac: fraction of the button radius (half side-length of inscribed square) defining the radius of the outine.
        """
        self._outline_frac = outline_frac if outline_frac is not None else  TOOL_BUTTONS['outline_frac']
        super().__init__(board, name, bbox, callbacks=callbacks, action_mouseup=action_mouseup, pinned=pinned,show_bbox=False)
        self._set_geom()


    def _set_geom(self):
        """
        Set the geometry of the button based on the color.
        """
        x_span, y_span = self._bbox['x'][1] - self._bbox['x'][0], self._bbox['y'][1] - self._bbox['y'][0]
        if x_span<0 or y_span <0:
            raise ValueError("Invalid bbox for button %s: %s" % (self.name, self._bbox))
        self._box_rad = min(x_span, y_span) / 2.
        self._circle_center = (self._bbox['x'][0] + x_span / 2, self._bbox['y'][0] + y_span / 2)
        self._outline_rad = self._box_rad * self._outline_frac
        self._select_points = get_circle_points(self._circle_center, self._outline_rad)
        logging.info("Set geom for %s using outline_frac %s, _rad %s" % (self.name, self._outline_frac, self._outline_rad))

    def render(self, img):
        if self.moused_over and not self.state:
            cv2.polylines(img, [floats_to_fixed(self._select_points)], True,
                          self._mouseover_color_v, lineType=cv2.LINE_AA, thickness=1,shift=PREC_BITS)
        elif self.state:
            cv2.polylines(img, [floats_to_fixed(self._select_points)], True,
                          self._selected_color_v, lineType=cv2.LINE_AA, thickness=1,shift=PREC_BITS)   
        self._draw_icon(img)

    @abstractmethod
    def _draw_icon(self, img):
        pass


class ColorButton(CircleButton):
    """
    A button representing a color the user can select.
    """

    def __init__(self, board, name, bbox, color_n, pinned=False, circle_frac = None):
        self._circle_frac = circle_frac if circle_frac is not None else COLOR_BUTTONS['circle_frac']
        self._color_n = color_n        
        self._color_v = COLORS_BGR[color_n]

        super().__init__(board, name, bbox, action_mouseup=False,
                         callbacks=(self._change_color,), pinned=pinned, outline_frac=COLOR_BUTTONS['outline_frac'])

    def _set_geom(self):
        super()._set_geom()
        self._circle_rad = self._circle_frac * self._box_rad

        self._color_circle_points = get_circle_points(self._circle_center, self._circle_rad)

    def _change_color(self, button, new_state, old_state):
        if new_state:
            self._board.tools.set_color(self._color_n)

    def _draw_icon(self, img):
        # draw color circle
        cv2.fillPoly(img, [floats_to_fixed(self._color_circle_points)],
                     self._color_v, lineType=cv2.LINE_AA,shift=PREC_BITS)

class ToolButton(CircleButton):
    """
    A button representing a tool the user can select.
    """

    def __init__(self, board, name, bbox, pinned=False, **kwargs):
        if name not in BUTTON_ARTISTS:
            raise ValueError("Invalid tool name, no artist: %s" % name)
        self._artist = BUTTON_ARTISTS[name](board, bbox)

        super().__init__(board, name, bbox, action_mouseup=False,
                         callbacks=(self._change_tool,), pinned=pinned, **kwargs)
        
    def move_to(self, xy, new_bbox=None):
        # move the button and the artist
        super().move_to(xy, new_bbox)
        self._artist.move_to(xy, new_bbox)

    def _change_tool(self, button, new_state, old_state):
        if new_state:
            self._board.tools.set_tool(self.name)

    def _draw_icon(self, img):
        self._artist.render(img)


    