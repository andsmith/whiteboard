import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, BOARD_LAYOUT, VECTOR_DEF
from board import Board
import logging
from windows import BoardWindow, ControlWindow

class Whiteboard(object):
    def __init__(self, state_file=None):
        logging.info("Starting Whiteboard...")
        
        self._board = Board()
        
        # Two windows, each with a view of the board, each 
        # tells the managers how to render their elements:
        self._board_window = BoardWindow(self._board)
        self._ctrl_window = ControlWindow(self._board)


    def run(self):

        while True:
            self._board_window.refresh()
            self._ctrl_window.refresh()

            key = cv2.waitKey(10) & 0xFF

            if key == 27:
                break
            else:
                self._board.keypress(key)

        cv2.destroyAllWindows()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Whiteboard().run()
