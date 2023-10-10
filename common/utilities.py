""" This module contains utility functions that are used by a variety of other modules. """
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


class Position:
    """The Position class holds the x and y coordinates of a player."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
