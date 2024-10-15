import cv2
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import sys

def _record_points(win_size):
    """
    Open a window.
    When the user clicks, start recording and plotting points (connected w/lines).
    When the user unclicks, stop recording and save the points in incrementing file numbers.
    """
    points = []
    recording = False
    img = np.zeros((win_size, win_size, 3), np.uint8)
    cv2.imshow('image', img)

    def save(points):
        f_num=0
        while os.path.exists(f'points{f_num}.json'):
            f_num+=1
        with open(f'points{f_num}.json', 'w') as f:
            json.dump(points, f)
        print(f'Saved points{f_num}.json')

    def draw_points(event, x, y, flags, param):
        nonlocal recording
        nonlocal points
        if event == cv2.EVENT_LBUTTONDOWN:
            recording = True
            points = [(x, y)]
        elif event == cv2.EVENT_MOUSEMOVE and recording:
            points.append((x, y))
            cv2.polylines(img, [np.array(points)], False, (255, 255, 255), 2)
            cv2.imshow('image', img)
            
        elif event == cv2.EVENT_LBUTTONUP:
            recording = False
            points.append((x, y))
            cv2.polylines(img, [np.array(points)], False, (255, 255, 255), 2)
            cv2.imshow('image', img)
            save(points)

    cv2.setMouseCallback('image', draw_points)
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            break
        if key == ord(' '):
            img = np.zeros((win_size, win_size, 3), np.uint8)

    cv2.destroyAllWindows()
    return points


if __name__=="__main__":
    _record_points(512)