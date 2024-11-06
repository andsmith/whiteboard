import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, BOARD_LAYOUT, VECTOR_DEF, EMPTY_BBOX, INIT_OPTIONS
import logging
from windows import UIWindow
import time
from board_view import BoardView
from vector_manager import VectorManager
from tools import ToolManager
from util import unit_to_abs_bbox
from buttons import ColorButton, ToolButton, ArtistButton, DialButton
from button_box import ButtonBox
from slider import Slider
import pprint
from popup_artists import TextSizeArtist, ThicknessArtist
# from zoom_view import ZoomViewControl


class WhiteboardApp(object):
    def __init__(self, state_file=None):
        logging.info("Starting Whiteboard...")

        self._vector_manager = VectorManager(state_file)
        self._tool_manager = ToolManager(self, self._vector_manager)
        self._tool_manager.set_color_thickness(INIT_OPTIONS['color'],INIT_OPTIONS['thickness'])
        self._tool_manager.set_text_size(INIT_OPTIONS['font_size'])
        views, zoom_controllers = self._make_zoom()

        self._windows = {'control': self._make_control_window(views['control'],
                                                              self._tool_manager,
                                                              self._vector_manager),

                         'board': self._make_board_window(views['board'],
                                                          self._tool_manager,
                                                          self._vector_manager)}
        self._win_titles = {win_kind: self._windows[win_kind].get_name_and_title()[1] for win_kind in self._windows}
        #  Added last, so mouse signals are sent to other controls first.
        # self._windows['control'].add_control(self._zoom_controllers['control'])
        # self._windows['board'].add_control(self._zoom_controllers['board'])

        self._options = {k: INIT_OPTIONS[k] for k in INIT_OPTIONS}
        #self.set_option('snap_to_grid', INIT_OPTIONS['snap_to_grid'])

    def get_option(self, option_name):
        return self._options[option_name]

    def set_option(self, option_name, value):
        logging.info("Whiteboard changed option: '%s'  -->  %s." % (option_name, value))
        self._options[option_name] = value

    def toggle_option(self, option_name):
        self.set_option(option_name, not self.get_option(option_name))

    def _make_zoom(self):
        """
        The views are the parts of the board that are visible in each window.

        Given the view in the board widow, and the placement of the zoomviewcontrol,
        Figure out the zoom/origin of the control window so it's zoomviewcontrol
        is centered in the control window w/the specified margin.


        :returns dict('control': BoardView, 'board': BoardView),
                dict('control': ZoomViewControl, 'board': ZoomViewControl)
        """
        ctrl_win_size = CONTROL_LAYOUT['win_size']

        board_view = BoardView('board',
                               BOARD_LAYOUT['win_size'],
                               BOARD_LAYOUT['init_origin'],
                               BOARD_LAYOUT['init_zoom'])

        # For now, just scale 2x  ###FIXME
        ctrl_view = BoardView('control',
                              ctrl_win_size,
                              BOARD_LAYOUT['init_origin'],
                              BOARD_LAYOUT['init_zoom'] * 1.3)

        return {'control': ctrl_view, 'board': board_view}, \
            {'control': None, 'board': None}

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
        tool_buttons = [[ToolButton(cw, tool_name, EMPTY_BBOX, outline_frac=1.2) if tool_name is not None else None
                         for tool_name in row]
                        for row in tool_name_grid]

        tool_button_box = unit_to_abs_bbox(CONTROL_LAYOUT['tool_box']['loc'], ctrl_win_size)
        tool_control = ButtonBox(cw, 'tool_button_box', tool_button_box, tool_buttons, exclusive=True)

        # command buttons
        command_name_grid = CONTROL_LAYOUT['command_box']['options']
        command_buttons = {'undo': ArtistButton(cw, 'undo', EMPTY_BBOX, callbacks=(self.undo,), states=(False, )),
                           'redo': ArtistButton(cw, 'redo', EMPTY_BBOX, callbacks=(self.redo,), states=(False, )),
                           'grid': ArtistButton(cw, 'grid', EMPTY_BBOX,
                                                callbacks=(lambda *_: self.toggle_option('show_grid'),),
                                                states=(True, False) if INIT_OPTIONS['show_grid'] else (False, True)),
                           'snap_to_grid': ArtistButton(cw, 'snap_to_grid', EMPTY_BBOX,
                                                        callbacks=(lambda *_: self.toggle_option('snap_to_grid'),),
                                                        states=(True, False) if INIT_OPTIONS['snap_to_grid'] else (False, True)),
                           'clear': ArtistButton(cw, 'clear', EMPTY_BBOX, callbacks=(self._vector_manager.clear,), states=(False, )),
                           'thickness': DialButton(cw, 'thickness', EMPTY_BBOX, dial_artist_t=ThicknessArtist, scale = 80.,
                                                   callbacks=(lambda _, x, __: self._tool_manager.set_color_thickness(None, int(x)),),
                                                   range=CONTROL_LAYOUT['command_box']['thickness_range'], 
                                                   init_val=self._tool_manager.get_color_thickness()[1]),
                           'text_size': DialButton(cw, 'text_size', EMPTY_BBOX, dial_artist_t=TextSizeArtist, scale = 12., 
                                                    callbacks=(lambda _, x, __: self._tool_manager.set_text_size(int(x)),),
                                                   range=[6, 48], init_val=self._tool_manager.get_text_size())
                           }
        
        command_buttons = [[command_buttons[command_name] if command_name is not None else None
                            for command_name in row]
                           for row in command_name_grid]
        command_button_bbox = unit_to_abs_bbox(CONTROL_LAYOUT['command_box']['loc'], ctrl_win_size)
        command_control = ButtonBox(cw, 'command_button_box', command_button_bbox,
                                    command_buttons, exclusive=False, show_bbox=False)

        # zoom slider
        zoom_slider_box = unit_to_abs_bbox(CONTROL_LAYOUT['zoom_slider']['loc'], ctrl_win_size)
        zoom_slider = Slider(cw, zoom_slider_box, 'control_zoom_slider', label_str=CONTROL_LAYOUT['zoom_slider']['label'],
                             orientation=CONTROL_LAYOUT['zoom_slider']['loc']['orientation'],
                             values=[.1, 20], init_val=view.get_scope()[0], show_bbox=False, valchange_callbacks=(cw.set_zoom,))

        # add controls to window
        cw.add_control(color_control)
        cw.add_control(tool_control)
        cw.add_control(zoom_slider)
        cw.add_control(command_control)

        return cw

    def undo(self, *_):
        logging.info("Undoing last action.")

    def redo(self, *_):
        logging.info("Redoing last action.")

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
        zoom_slider = Slider(bw, zoom_slider_box, 'board_zoom_slider', label_str=BOARD_LAYOUT['zoom_bar']['label'],
                             orientation=BOARD_LAYOUT['zoom_bar']['loc']['orientation'],
                             values=[1, 20], init_val=view.get_scope()[0], show_bbox=False, valchange_callbacks=(bw.set_zoom,))
        bw.add_control(zoom_slider)
        return bw

    def run(self):

        for window in self._windows:
            self._windows[window].start()

        n_frames, t_start = 0, time.perf_counter()
        while True:

            # Redraw windows:
            # for win_name in self._windows:
            #    self._windows[win_name].refresh()
            self._windows['control'].refresh(options=dict(show_grid=self.get_option('show_grid')))
            self._windows['board'].refresh(options=dict(show_grid=self.get_option('show_grid')))

            # Flush to screen & handle keypresses:
            key = cv2.waitKey(1) & 0xFF
            if not self._keypress(key):
                break

            # Report FPS:
            n_frames += 1
            t = time.perf_counter()
            if t - t_start > 2:
                logging.info("FPS: %d" % (n_frames / (t - t_start)))

                def get_vec_strs(vs):
                    strs = []
                    for v in vs:
                        strs.append("%s: (H: %i) (%.2f, %.2f) -> (%.2f, %.2f)" % (v.name, 1 if v.highlighted else 0,
                                                                                  v._points[0][0], v._points[0][1],
                                                                                  v._points[-1][0], v._points[-1][1]))
                    return strs
                # Report vectors:
                vecs = get_vec_strs(self._vector_manager._vectors)
                active_vecs = get_vec_strs(self._vector_manager._vecs_in_progress)
                logging.info("Vectors: %s" % pprint.pformat(vecs))
                logging.info("Active vectors: %s" % pprint.pformat(active_vecs))

                n_frames, t_start = 0, t

        cv2.destroyAllWindows()

    def _keypress(self, key):
        if key == 27 or key == ord('q'):
            print("User quit.")
            return False
        for win_kind in self._windows:
            if cv2.getWindowProperty(self._win_titles[win_kind], cv2.WND_PROP_VISIBLE):
                if not self._windows[win_kind].keypress(key):
                    break
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    WhiteboardApp().run()
