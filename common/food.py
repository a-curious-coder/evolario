import math

import pygame
from omegaconf import DictConfig

from common.utilities import Position, random_position, random_rgb


class FoodCell:
    """
    The Food class represents a single piece of food in the game.
    Each food has a position, as well as a colour.
    """

    def __init__(self, cfg: DictConfig, position: Position):
        """
        Initialize a new Food instance.

        Parameters:
            position (Position): The position of the food.
            colour (Tuple[int, int, int]): The colour of the food as an (R, G, B) tuple.
        """
        self.radius = cfg.food_radius
        self.position = position
        self.colour = random_rgb()

    def draw(self, screen):
        """Draws the food on the game screen as a circle."""
        pygame.draw.circle(
            screen, self.colour, (self.position.x, self.position.y), self.radius
        )


class FoodCellManager:
    """
    The FoodManager class encapsulates the management of multiple
    pieces of Food in the game. It allows adding, removing,
    fetching all food items and drawing them.
    """

    def __init__(self, cfg: DictConfig, player_manager):
        """
        Initializes a new FoodManager instance.
        """
        self.cfg = cfg
        self.food_cfg = cfg.food
        self.food_cells = []
        self.player_manager = player_manager

    def add(self, position):
        """
        Adds a new piece of Food to the FoodManager's list.

        :param x: The x-coordinate of the new food
        :param y: The y-coordinate of the new food
        :param colour: The colour of the new food
        """
        self.food_cells.append(FoodCell(self.food_cfg, position))

    def remove(self, index):
        """
        Removes a piece of Food from the FoodManager's list
        at the specified index.

        :param index: The index in the list from which to remove the food
        """
        del self.food_cells[index]

    def create_food(self, n):
        """Creates food cells on the map

        :param n: The number of food cells to create
        """
        for _ in range(n):
            while True:
                stop = True
                position = random_position(self.cfg.w, self.cfg.h)
                for player in self.player_manager.players.items():
                    p = self.player_manager.players[player]
                    dis = math.sqrt(
                        (position.x - p.position.x) ** 2
                        + (position.y - p.position.y) ** 2
                    )
                    if dis <= self.cfg.player.player_radius + p.radius:
                        stop = False
                if stop:
                    break

            self.food_cells.append((position.x, position.y, random_rgb()))

    def get_all(self):
        """
        Fetches all the pieces of Food managed by the FoodManager.

        :return: The list of all food pieces
        """
        return self.food_cells

    def draw(self, screen):
        """4
        Draws each piece of Food on the game screen.
        """
        for food in self.food_cells:
            food.draw(screen)
