import math
import random

import pygame

pygame.font.init()
from omegaconf import DictConfig

from common.utilities import Position, random_rgb


class Player:
    """
    The Player class holds the information for a single player.
    Each player has a name, position, score and colour.
    """

    def __init__(self, cfg: DictConfig, id, name, position):
        """
        Initialize a new Player instance.

        Parameters:
            name (str): The name of the player .
            position (Position): The position of the player.
            score (int): The score of the player.
            colour (Tuple[int, int, int]): The colour of the player as an (R, G, B) tuple.
        """
        self.cfg = cfg
        self.player_config = cfg.player
        self.score = 0
        self.id = id
        self.name = name
        self.position = position
        self.colour = random_rgb()
        self.vel = self.player_config.start_velocity
        self.radius = self.player_config.radius

    def draw(self, screen):
        """Draws the player on the game screen with a circle representing the player and their name.

        Parameters:
            screen (pygame.Surface): The game screen.
        """
        pygame.draw.circle(
            screen,
            self.colour,
            (self.position.x, self.position.y),
            self.player_config.radius + round(self.score),
        )

    def move(self):
        """Moves the player based on the key presses."""
        keys = pygame.key.get_pressed()
        # movement based on key presses
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            pos = self.position.x - self.vel - self.player_config.radius - self.score
            if pos >= 0:
                self.position.x = self.position.x - self.vel

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            pos = self.position.x + self.vel + self.player_config.radius + self.score
            if pos <= self.cfg.width:
                self.position.x = self.position.x + self.vel

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            pos = self.position.y - self.vel - self.player_config.radius - self.score
            if pos >= 0:
                self.position.y = self.position.y - self.vel

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            pos = self.position.y + self.vel + self.player_config.radius + self.score
            if pos <= self.cfg.height:
                self.position.y = self.position.y + self.vel

    def update_speed(self, vel):
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
        self.player_config = cfg.player
        self.players: dict[str, Player] = {}
        self.name_font = pygame.font.SysFont("arial", 20)

    def add(self, player_id, name):
        """
        Adds a new Player instance to the players dictionary.

        Parameters:
            name (str): The name of the player.
            x (int): The x-coordinate of the player.
            y (int): The y-coordinate of the player.
            score (int): The score of the player.
        """
        position = self.get_start_location()
        self.players[player_id] = Player(self.cfg, player_id, name, position)

    def update(self, player_id, position, score, colour):
        """
        Updates the information of a specific player.

        Parameters:
            name (str): The name of the player.
            x (int): The new x-coordinate of the player.
            y (int): The new y-coordinate of the player.
            score (int): The new score of the player.
            colour (Tuple[int,int,int]): The new colour of the player as an (R, G, B) tuple.
        """
        self.players[player_id].position = position
        self.players[player_id].score = score
        self.players[player_id].colour = colour

    def remove(self, player_id):
        """
        Removes a player from the players dictionary.

        Parameters:
            name (str): The name of the player to be removed.
        """
        del self.players[player_id]

    def get(self, player_id):
        """
        Fetches a specific player from the players dictionary.

        Parameters:
            name (str): The name of the player to be fetched.

        Returns:
            Player: The player instance with the specified name.
        """
        return self.players[player_id]

    def get_all(self):
        """
        Fetches all the players.

        Returns:
            dict: A dictionary of all player instances.
        """
        return self.players

    def handle_move_command(self, data, player_id):
        try:
            split_data = data.split(" ")
            x = int(split_data[1])
            y = int(split_data[2])
            self.players[player_id].position.x = x
            self.players[player_id].position.y = y
        except Exception as e:
            print(e)
            input("Press enter to continue...")

    def get_start_location(self):
        """
        picks a start location for a player based on other player
        locations. It will ensure it does not spawn inside another player

        :param players: dict
        :return: tuple (x,y)
        """
        while True:
            stop = True
            x = random.randrange(0, self.cfg.width)
            y = random.randrange(0, self.cfg.height)
            for player in self.players.values():
                dis = math.sqrt(
                    (x - player.position.x) ** 2 + (y - player.position.y) ** 2
                )
                if dis <= self.player_config.radius + player.score:
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
            player_name = self.name_font.render(player.name, 1, (0, 0, 0))
            screen.blit(
                player_name,
                (
                    player.position.x - player_name.get_width() / 2,
                    player.position.y - player_name.get_height() / 2,
                ),
            )
