import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, BOARD_LAYOUT, VECTORS
from board import Board
import logging
from windows import BoardWindow, ControlWindow
from controls import ControlManager
from vector_manager import VectorManager
from tools import ToolManager

class Whiteboard(object):
    def __init__(self, state_file=None):
        logging.info("Starting Whiteboard...")
        
        self._board = Board()

        # Three kinds of UI elements, can talk to each other via the shared board object:
        self._board.vectors = VectorManager(self._board, state_file)
        self._board.controls = ControlManager(self._board)
        self._board.tools = ToolManager(self._board)
        
        # Two windows, each with a view of the board, each 
        # tell the managers how to render their elements:
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
