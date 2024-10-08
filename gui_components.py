"""
Define some lightweight UI elements for the app.
"""
import numpy as np
import cv2
from abc import ABC, abstractmethod


class Component(ABC):
    """
    Abstract class for all UI components.
    """

    def __init__(self, canvas):
        self.canvas = canvas
        self.active = True

    @abstractmethod
    def render(self, img):
        """
        Draw the component on the image.
        """
        pass

    @abstractmethod
    def mouse_event(self, event, x, y, flags, param):
        """
        Handle mouse events.
        """
        pass

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

class Action(object):
    """
    Represents a change in the canvas (not the UI)
    """