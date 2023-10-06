import contextlib

with contextlib.redirect_stdout(None):
    import pygame

import os
import random

from client import Client

pygame.font.init()
# Set window to center of screen
pygame.display.set_caption("Evolario")

# Constants
PLAYER_RADIUS = 20
START_VEL = 3
FOOD_RADIUS = 5

TRANSPARENCY = 50
GRIDLINE_THICKNESS = 2
GRIDLINE_SPACING = 40

W, H = 1920, 1080

NAME_FONT = pygame.font.SysFont("arial", 20)
TIME_FONT = pygame.font.SysFont("arial", 30)
SCORE_FONT = pygame.font.SysFont("arial", 22)

COLOURS = [
    (255, 0, 0),
    (255, 128, 0),
    (255, 255, 0),
    (128, 255, 0),
    (0, 255, 0),
    (0, 255, 128),
    (0, 255, 255),
    (0, 128, 255),
    (0, 0, 255),
    (0, 0, 255),
    (128, 0, 255),
    (255, 0, 255),
    (255, 0, 128),
    (128, 128, 128),
    (0, 0, 0),
]
# Make window start in center of screen
os.environ["SDL_VIDEO_CENTERED"] = "1"

# setup pygame window
SCREEN = pygame.display.set_mode((W, H))


# FUNCTIONS
def convert_time(t):
    """
    converts a time given in seconds to a time in
    minutes

    :param t: int
    :return: string
    """
    if type(t) == str:
        return t

    if int(t) < 60:
        return str(t) + "s"
    else:
        minutes = str(t // 60)
        seconds = str(t % 60)

        if int(seconds) < 10:
            seconds = "0" + seconds

        return minutes + ":" + seconds


def draw_window(player_manager, game_time, score):
    """
    draws each frame
    :return: None
    """
    players = player_manager.get_all()
    # Set background colour
    SCREEN.fill((255, 255, 255))
    draw_grid()
    # get players from player manager and sort them by score

    # draw scoreboard
    sort_players = list(reversed(sorted(players, key=lambda x: players[x]["score"])))
    title = TIME_FONT.render("Scoreboard", 1, (0, 0, 0))
    start_y = 25
    x = W - title.get_width() - 10
    SCREEN.blit(title, (x, 5))

    ran = min(len(players), 3)
    for count, i in enumerate(sort_players[:ran]):
        text = SCORE_FONT.render(
            str(count + 1) + ". " + str(players[i]["name"]), 1, (0, 0, 0)
        )
        if count == 0:
            SCREEN.blit(text, (x, start_y + (1 * 25)))
        else:
            SCREEN.blit(text, (x, start_y + (count * 25)))

    # draw time
    text = TIME_FONT.render("Time: " + convert_time(game_time), 1, (0, 0, 0))
    SCREEN.blit(text, (10, 10))
    # draw score
    text = TIME_FONT.render("Score: " + str(round(score)), 1, (0, 0, 0))
    SCREEN.blit(text, (10, 15 + text.get_height()))


def draw_grid():
    for i in range(0, H, GRIDLINE_SPACING):
        horizontal_line = pygame.Surface((W, GRIDLINE_THICKNESS), pygame.SRCALPHA)
        horizontal_line.fill(
            (184, 184, 184, TRANSPARENCY)
        )  # You can change the 100 depending on what transparency it is.
        SCREEN.blit(horizontal_line, (0, i - 1))

    for i in range(0, W, GRIDLINE_SPACING):
        vertical_line = pygame.Surface((GRIDLINE_THICKNESS, H), pygame.SRCALPHA)
        vertical_line.fill(
            (184, 184, 184, TRANSPARENCY)
        )  # You can change the 100 depending on what transparency it is.
        SCREEN.blit(vertical_line, (i - 1, 0))


class Position:
    """The Position class holds the x and y coordinates of a player."""

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Player:
    """
    The Player class holds the information for a single player.
    Each player has a name, position, score and colour.
    """

    def __init__(self, name, position, score):
        """
        Initialize a new Player instance.

        Parameters:
            name (str): The name of the player.
            position (Position): The position of the player.
            score (int): The score of the player.
            colour (Tuple[int, int, int]): The colour of the player as an (R, G, B) tuple.
        """
        self.name = name
        self.position = position
        self.score = score
        self.colour = random.choice(COLOURS)
        self.vel = START_VEL

    def move(self):
        keys = pygame.key.get_pressed()
        # movement based on key presses
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if self.position.x - self.vel - PLAYER_RADIUS - self.score >= 0:
                self.position.x = self.position.x - self.vel

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if self.position.x + self.vel + PLAYER_RADIUS + self.score <= W:
                self.position.x = self.position.x + self.vel

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if self.position.y - self.vel - PLAYER_RADIUS - self.score >= 0:
                self.position.y = self.position.y - self.vel

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if self.position.y + self.vel + PLAYER_RADIUS + self.score <= H:
                self.position.y = self.position.y + self.vel

    def update_speed(self, vel):
        self.vel = vel

    def get_x(self):
        return self.position.x

    def get_y(self):
        return self.position.y


class PlayerManager:
    """
    The PlayerManager class maintains the information of all players.
    It supports operations such as adding, updating, removing players and delivering player information.
    """

    def __init__(self):
        """
        Initializes a new PlayerManager instance.
        """
        self.players = {}

    def add(self, name, position, score):
        """
        Adds a new Player instance to the players dictionary.

        Parameters:
            name (str): The name of the player.
            x (int): The x-coordinate of the player.
            y (int): The y-coordinate of the player.
            score (int): The score of the player.
        """
        self.players[name] = Player(name, position, score)

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

    def draw(self):
        """
        Draw each player on the game screen with a circle representing the player and their name.
        """
        for _, player in self.players.items():
            pygame.draw.circle(
                SCREEN,
                player.colour,
                (player.x, player.y),
                PLAYER_RADIUS + round(player.score),
            )
            player_name = NAME_FONT.render(player.name, 1, (0, 0, 0))
            SCREEN.blit(
                player_name,
                (
                    player.x - player_name.get_width() / 2,
                    player.y - player_name.get_height() / 2,
                ),
            )


class FoodCell:
    """
    The Food class represents a single piece of food in the game.
    Each food has a position, as well as a colour.
    """

    def __init__(self, position, colour):
        """
        Initialize a new Food instance.

        Parameters:
            position (Position): The position of the food.
            colour (Tuple[int, int, int]): The colour of the food as an (R, G, B) tuple.
        """
        self.position = position
        self.colour = colour


class FoodCellManager:
    """
    The FoodManager class encapsulates the management of multiple
    pieces of Food in the game. It allows adding, removing,
    fetching all food items and drawing them.
    """

    def __init__(self):
        """
        Initializes a new FoodManager instance.
        """
        self.food_cells = []

    def add(self, position, colour):
        """
        Adds a new piece of Food to the FoodManager's list.

        :param x: The x-coordinate of the new food
        :param y: The y-coordinate of the new food
        :param colour: The colour of the new food
        """
        self.food_cells.append(FoodCell(position, colour))

    def remove(self, index):
        """
        Removes a piece of Food from the FoodManager's list
        at the specified index.

        :param index: The index in the list from which to remove the food
        """
        del self.food_cells[index]

    def get_all(self):
        """
        Fetches all the pieces of Food managed by the FoodManager.

        :return: The list of all food pieces
        """
        return self.food_cells

    def draw(self):
        """
        Draws each piece of Food on the game screen.
        """
        for food in self.food_cells:
            pygame.draw.circle(SCREEN, food.colour, (food.x, food.y), FOOD_RADIUS)


def main(player_name):
    """
    function for running the game,
    includes the main loop of the game

    :param players: a list of dicts represting a player
    :return: None
    """
    player_manager = PlayerManager()
    food_manager = FoodCellManager()

    client = Client()
    _id = client.connect(player_name)
    food_manager.food_cells, player_manager.players, game_time = client.send("get")
    clock = pygame.time.Clock()
    # Get current player
    player = player_manager.get(_id)

    run = True
    while run:
        # limit the game to 30 frames per second
        clock.tick(30)

        # Calculate velocity based on score
        vel = max(START_VEL - round(player.score / 14), 1)
        player.update_speed(vel)

        # move player
        player.move()

        # create data to send to server
        data = "move " + str(player.get_x()) + " " + str(player.get_y())

        # Send new data to server
        client.send(data)

        # Get current information from server
        food_manager.food_cells, player_manager.players, game_time = client.send("get")

        for event in pygame.event.get():
            # if user hits red x button close window
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                # if user hits a escape key close program
                if event.key == pygame.K_ESCAPE:
                    run = False

        # Draw game window
        draw_window(player_manager, game_time, player.score)
        player_manager.draw()
        food_manager.draw()

        pygame.display.update()

    client.disconnect()
    pygame.quit()
    quit()


try:
    # start game
    main("Human")
except KeyboardInterrupt as k:
    print(k.__class__.__name__)
