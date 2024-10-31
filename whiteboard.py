import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, BOARD_LAYOUT, VECTOR_DEF
import logging
from windows import UIWindow
import time
from board_view import BoardView
from vector_manager import VectorManager
from tools import ToolManager
from util import unit_to_abs_bbox


class WhiteboardApp(object):
    def __init__(self, state_file=None):
        logging.info("Starting Whiteboard...")

        self._vector_manager = VectorManager(state_file)
        self._tool_manager = ToolManager(self._vector_manager)
        self._views, self._zoom_controlers = self._make_views()
        self._windows = {'control': self._make_control_window(self._views['control'],
                                                              self._tool_manager,
                                                              self._vector_manager),

                         'board': self._make_board_window(self._views['board'],
                                                          self._tool_manager,
                                                          self._vector_manager)}
        
    def _get_control_view_from_board_view(self, board_view, zoom_bbox_px):
        """
        Given the view of the whiteboard from the board window, 
        the bbox of the zoom control in the board window, and the placement of the
        zoom control in the control window, calculate the view of the whiteboard in the control window.
        (zoom/origin)
        """
        margin_frac = CONTROL_LAYOUT['margin_frac']
        control_win_wh = np.array(CONTROL_LAYOUT['win_size'])
        control_box_wh = control_win_wh * (1.0 - 2 * margin_frac)

    def _make_views(self):
        """
        The views are the parts of the board that are visible in each window.

        Calculate in this order:
            The board-window view is determined by its window size, the zoom and origin.
            The origial placement of the ZoomViewControl within the board window is set in the
            layout.  
            The control-window's view are set by the placement/shape of the ZoomViewControl
            so that it fits within the control-window.

        :returns dict('control': BoardView, 'board': BoardView),
                dict('control': ZoomViewControl, 'board': ZoomViewControl)
        """
        board_view = BoardView('board',
                               BOARD_LAYOUT['win_size'],
                               BOARD_LAYOUT['init_origin'],
                               BOARD_LAYOUT['init_zoom'])
        board_zc_bbox_px = unit_to_abs_bbox(BOARD_LAYOUT['init_zoom_window_extent'],
                                            BOARD_LAYOUT['win_size'])
        control_view = self._get_control_view_from_board_view(board_view, board_zc_bbox_px)
        
        
        zoom_control = ZoomViewControl(board_view, BOARD_LAYOUT['zoom_bar'])
        return {'control': board_view, 'board': board_view}, {'control': zoom_control, 'board': zoom_control}

    def _make_control_window(self, tool_manager, vector_manager):
        # Create the

        # make the window
        cw = UIWindow('control',
                      CONTROL_LAYOUT['win_name'],
                      CONTROL_LAYOUT['win_size'],
                      bkg_color_n=BOARD_LAYOUT['bkg_color'])
        # make the controls, add them to the window
        

    def run(self):
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
