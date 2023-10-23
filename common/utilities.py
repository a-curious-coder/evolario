""" This module contains utility functions that are used by a variety of other modules. """
import math
import random


def random_rgb():
    """Returns a random RGB tuple."""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return (r, g, b)


def random_position(w, h):
    """Returns a random Position tuple."""
    x = random.randint(0, w)
    y = random.randint(0, h)
    return Position(x, y)


def calculate_distance(x1, y1, x2, y2):
    """
    Calculates the distance between two points in 2D space

    Parameters:
        x1 (int): The x-coordinate of the first point.
        y1 (int): The y-coordinate of the first point.
        x2 (int): The x-coordinate of the second point.
        y2 (int): The y-coordinate of the second point.
    """
    return math.hypot(x2 - x1, y2 - y1)


class Position:
    """The Position class holds the x and y coordinates of a player."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    # Write a getter that returns the x and y coordinates as a tuple
    def get(self):
        """Returns the x and y coordinates as a tuple."""
        return (self.x, self.y)
