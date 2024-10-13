import cv2
import numpy as np
from layout import COLORS_RGB, SLIDERS, CONTROL_LAYOUT, CANVAS_LAYOUT. VECTORS
from canvas import Board
import logging


class Whiteboard(object):
    def __init__(self, state_file=None):

        logging.info("Starting Whiteboard...")

        self._canv_win_name, canv_win_size = CANVAS_LAYOUT['name'], CANVAS_LAYOUT['size']
        self._ctrl_win_name, ctrl_win_size = CONTROL_LAYOUT['name'], CONTROL_LAYOUT['size']

        self._canvas = Board(canv_win_size, ctrl_win_size)

        if state_file is not None:
            self._canvas.load(state_file)

        cv2.namedWindow(self._canv_win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._canv_win_name, canv_win_size[0], canv_win_size[1])
        cv2.setMouseCallback(self._canv_win_name, self._canvas.canv_mouse_callback)

        cv2.namedWindow(self._ctrl_win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._ctrl_win_name, ctrl_win_size[0], ctrl_win_size[1])
        cv2.setMouseCallback(self._ctrl_win_name, self._canvas.ctrl_mouse_callback)

    def run(self):
        while True:
            canv_frame, ctrl_frame = self._canvas.get_frames()
            cv2.imshow(self._canv_win_name, canv_frame)
            cv2.imshow(self._ctrl_win_name, ctrl_frame)

            key = cv2.waitKey(10) & 0xFF
            if key == 27:
                break
            else:
                self._canvas.keypress(key)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Whiteboard().run()
