import math
import random

import pygame
from omegaconf import DictConfig

from common.utilities import Position, random_rgb


class Player:
    """
    The Player class holds the information for a single player.
    Each player has a name, position, score and colour.
    """

    def __init__(self, cfg: DictConfig, name, position):
        """
        Initialize a new Player instance.

        Parameters:
            name (str): The name of the player .
            position (Position): The position of the player.
            score (int): The score of the player.
            colour (Tuple[int, int, int]): The colour of the player as an (R, G, B) tuple.
        """
        self.cfg = cfg
        self.score = 0
        self.name = name
        self.position = position
        self.colour = random_rgb()
        self.vel = self.cfg.start_velocity
        self.radius = self.cfg.player_radius
        self.name_font = pygame.font.SysFont("arial", 20)

    def draw(self, screen):
        """Draws the player on the game screen with a circle representing the player and their name.

        Parameters:
            screen (pygame.Surface): The game screen.
        """
        pygame.draw.circle(
            screen,
            self.colour,
            (self.position.x, self.position.y),
            self.cfg.player_radius + round(self.score),
        )
        player_name = self.name_font.render(self.name, 1, (0, 0, 0))
        screen.blit(
            player_name,
            (
                self.position.x - player_name.get_width() / 2,
                self.position.y - player_name.get_height() / 2,
            ),
        )

    def move(self):
        """Moves the player based on the key presses."""
        keys = pygame.key.get_pressed()
        # movement based on key presses
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            pos = self.position.x - self.vel - self.cfg.player_radius - self.score
            if pos >= 0:
                self.position.x = self.position.x - self.vel

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            pos = self.position.x + self.vel + self.cfg.player_radius + self.score
            if pos <= self.cfg.width:
                self.position.x = self.position.x + self.vel

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            pos = self.position.y - self.vel - self.cfg.player_radius - self.score
            if pos >= 0:
                self.position.y = self.position.y - self.vel

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            pos = self.position.y + self.vel + self.cfg.player_radius + self.score
            if pos <= self.cfg.height:
                self.position.y = self.position.y + self.vel

    def update_velocity(self, vel):
        """Updates the velocity of the player.

        Parameters:
            vel (int): The new velocity of the player.
        """
        self.vel = vel

    def get_x(self):
        """Fetches the x-coordinate of the player."""
        return self.position.x

    def get_y(self):
        """Fetches the y-coordinate of the player."""
        return self.position.y


class PlayerManager:
    """
    The PlayerManager class maintains the information of all players.
    It supports operations such as adding, updating, removing players and delivering player information.
    """

    def __init__(self, cfg: DictConfig):
        """
        Initializes a new PlayerManager instance.
        """
        self.cfg = cfg
        self.players: dict[str, Player] = {}

    def add(self, name):
        """
        Adds a new Player instance to the players dictionary.

        Parameters:
            name (str): The name of the player.
            x (int): The x-coordinate of the player.
            y (int): The y-coordinate of the player.
            score (int): The score of the player.
        """
        position = self._get_start_location()
        self.players[name] = Player(self.cfg, name, position)

    def update(self, name, position, score, colour):
        """
        Updates the information of a specific player.

        Parameters:
            name (str): The name of the player.
            x (int): The new x-coordinate of the player.
            y (int): The new y-coordinate of the player.
            score (int): The new score of the player.
            colour (Tuple[int,int,int]): The new colour of the player as an (R, G, B) tuple.
        """
        self.players[name].position = position
        self.players[name].score = score
        self.players[name].colour = colour

    def remove(self, name):
        """
        Removes a player from the players dictionary.

        Parameters:
            name (str): The name of the player to be removed.
        """
        del self.players[name]

    def get(self, name):
        """
        Fetches a specific player from the players dictionary.

        Parameters:
            name (str): The name of the player to be fetched.

        Returns:
            Player: The player instance with the specified name.
        """
        return self.players[name]

    def get_all(self):
        """
        Fetches all the players.

        Returns:
            dict: A dictionary of all player instances.
        """
        return self.players

    def handle_move_command(self, data, player_id):
        split_data = data.split(" ")
        x = int(split_data[1])
        y = int(split_data[2])
        self.players[player_id].position.x = x
        self.players[player_id].position.y = y

    def _get_start_location(self):
        """
        picks a start location for a player based on other player
        locations. It will ensure it does not spawn inside another player

        :param players: dict
        :return: tuple (x,y)
        """
        while True:
            stop = True
            x = random.randrange(0, self.cfg.w)
            y = random.randrange(0, self.cfg.h)
            for player in self.players.items():
                p = self.players[player]
                dis = math.sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2)
                if dis <= self.cfg.player_radius + p["score"]:
                    stop = False
                    break
            if stop:
                break
        return Position(x, y)

    def draw(self, screen):
        """
        Draw each player on the game screen with a circle representing the player and their name.
        """
        for _, player in self.players.items():
            player.draw(screen)
