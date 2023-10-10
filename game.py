import contextlib

import hydra
from omegaconf import DictConfig

with contextlib.redirect_stdout(None):
    import pygame

import os

from client.client import Client
from common.food import FoodCellManager
from common.player import PlayerManager

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


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    """
    function for running the game,
    includes the main loop of the game

    :param players: a list of dicts represting a player
    :return: None
    """
    print(os.getcwd())
    player_name = "Human"
    player_manager = PlayerManager(cfg.player)
    food_manager = FoodCellManager(cfg.food)

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


if __name__ == "__main__":
    main()
