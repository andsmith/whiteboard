import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, BOARD_LAYOUT, VECTOR_DEF, EMPTY_BBOX
import logging
from windows import UIWindow
import time
from board_view import BoardView
from vector_manager import VectorManager
from tools import ToolManager
from util import unit_to_abs_bbox
from buttons import ColorButton, ToolButton
from button_box import ButtonBox
from slider import Slider
from zoom_view import ZoomViewControl


class WhiteboardApp(object):
    def __init__(self, state_file=None):
        logging.info("Starting Whiteboard...")

        self._vector_manager = VectorManager(state_file)
        self._tool_manager = ToolManager(self._vector_manager)
        self._zoom_controllers = self._make_zoom_views()

        self._windows = {'control': self._make_control_window(self._views['control'],
                                                              self._tool_manager,
                                                              self._vector_manager),

                         'board': self._make_board_window(self._views['board'],
                                                          self._tool_manager,
                                                          self._vector_manager)}

        #  Added last, so mouse signals are sent to other controls first.
        self._windows['control'].add_control(self._zoom_controllers['control'])
        self._windows['board'].add_control(self._zoom_controllers['board'])

    def _make_views(self):
        """
        The views are the parts of the board that are visible in each window.

        Given the view in the board widow, and the placement of the zoomviewcontrol,
        Figure out the zoom/origin of the control window so it's zoomviewcontrol
        is centered in the control window w/the specified margin.


        :returns dict('control': BoardView, 'board': BoardView),
                dict('control': ZoomViewControl, 'board': ZoomViewControl)
        """
        board_view = BoardView('board',
                               BOARD_LAYOUT['win_size'],
                               BOARD_LAYOUT['init_origin'],
                               BOARD_LAYOUT['init_zoom'])

        board_zc_bbox_px = unit_to_abs_bbox(BOARD_LAYOUT['init_zoom_window_extent'],
                                            BOARD_LAYOUT['win_size'])

        zoom_aspect = (board_zc_bbox_px['x'][1] - board_zc_bbox_px['x'][0]) / \
            (board_zc_bbox_px['y'][1] - board_zc_bbox_px['y'][0])

        zoom_control = ZoomViewControl(board_view, BOARD_LAYOUT['zoom_bar'])
        return {'control': board_view, 'board': board_view}, {'control': zoom_control, 'board': zoom_control}

    def _make_control_window(self, view, tool_manager, vector_manager):
        ctrl_win_size = CONTROL_LAYOUT['win_size']
        cw = UIWindow('control',
                      view,
                      vector_manager,
                      tool_manager,
                      title=CONTROL_LAYOUT['win_name'],
                      window_size=ctrl_win_size,
                      bkg_color_n=BOARD_LAYOUT['bkg_color'])

        # Color buttons
        color_name_grid = CONTROL_LAYOUT['color_box']['options']
        color_buttons = [[ColorButton(cw, "CB: %s" % (color_name,), EMPTY_BBOX, color_name)
                          for color_name in row]
                         for row in color_name_grid]
        color_button_bbox = unit_to_abs_bbox(CONTROL_LAYOUT['color_box']['loc'], ctrl_win_size)
        color_control = ButtonBox(cw, 'color_button_box', color_button_bbox, color_buttons, exclusive=True)

        # Tool buttons
        tool_name_grid = CONTROL_LAYOUT['tool_box']['options']
        tool_buttons = [[ToolButton(cw, "TB: %s" % (tool_name,), EMPTY_BBOX, tool_name)
                         for tool_name in row]
                        for row in tool_name_grid]
        tool_button_box = unit_to_abs_bbox(CONTROL_LAYOUT['tool_box']['loc'], ctrl_win_size)
        tool_control = ButtonBox(cw, 'tool_button_box', tool_button_box, tool_buttons, exclusive=True)

        # zoom slider
        zoom_slider_box = unit_to_abs_bbox(CONTROL_LAYOUT['zoom_slider']['loc'], ctrl_win_size)
        zoom_slider = Slider(cw, zoom_slider_box, 'control_zoom_slider',
                             orientation=CONTROL_LAYOUT['zoom_slider']['orientation'],
                             values=[-10, 10], init_pos=0.5)

        # add controls to window
        cw.add_control(color_control)
        cw.add_control(tool_control)
        cw.add_control(zoom_slider)


        return cw

    def _make_board_window(self, view, tool_manager, vector_manager):
        board_win_size = BOARD_LAYOUT['win_size']
        bw = UIWindow('board',
                       view,
                       vector_manager,
                       tool_manager,
                       title=BOARD_LAYOUT['win_name'],
                       window_size=board_win_size,
                       bkg_color_n=BOARD_LAYOUT['bkg_color'])
        
        # zoom slider
        zoom_slider_box = unit_to_abs_bbox(BOARD_LAYOUT['zoom_bar']['loc'], board_win_size)
        zoom_slider = Slider(bw, zoom_slider_box, 'board_zoom_slider',
                             orientation=BOARD_LAYOUT['zoom_bar']['orientation'],
                             values=[-10, 10], init_pos=0.5)
        bw.add_control(zoom_slider)
        return bw

    def run(self):

        for window in self._windows:
            self._windows[window].start()

        n_frames, t_start = 0, time.perf_counter()
        while True:

            # Redraw windows:
            for win_name in self._windows:
                self._windows[win_name].refresh()

            # Flush to screen & handle keypresses:
            key = cv2.waitKey(1) & 0xFF
            if not self._keypress(key):
                break

            # Report FPS:
            n_frames += 1
            t = time.perf_counter()
            if t - t_start > 2:
                logging.info("FPS: %d" % (n_frames / (t - t_start)))
                n_frames, t_start = 0, t

        cv2.destroyAllWindows()

    def _keypress(self, key):
        if key == 27 or key == ord('q'):
            return False
        for win_kind in self._windows:
            if cv2.getWindowProperty(self._win_names[win_kind], cv2.WND_PROP_VISIBLE):
                self._windows[win_kind].keypress(key)
                break


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    WhiteboardApp().run()
