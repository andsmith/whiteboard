import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, BOARD_LAYOUT, VECTOR_DEF
from board import Board
import logging
from windows import BoardWindow, ControlWindow
import time


class Whiteboard(object):
    def __init__(self, state_file=None):
        logging.info("Starting Whiteboard...")

        self._board = Board()  # board creates managers
        self._board_window = BoardWindow(self._board)
        self._ctrl_window = ControlWindow(self._board)

    def run(self):
        n_frames, t_start = 0, time.perf_counter()

        while True:

            # Redraw windows:
            self._board_window.refresh()
            self._ctrl_window.refresh()

            # Flush to screen & handle keypresses:
            key = cv2.waitKey(10) & 0xFF
            if key == 27:
                break
            else:
                self._board.keypress(key)

            # Report FPS:
            n_frames += 1   
            t = time.perf_counter()
            if t - t_start > 2:
                logging.info("FPS: %d" % (n_frames / (t - t_start)))
                n_frames, t_start = 0, t

        cv2.destroyAllWindows()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Whiteboard().run()
