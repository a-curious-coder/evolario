import contextlib

import hydra
from omegaconf import DictConfig

with contextlib.redirect_stdout(None):
    import pygame

import os
import traceback

from client.client import Client
from common.food import FoodCellManager
from common.player import PlayerManager

pygame.font.init()
# Set window to center of screen
pygame.display.set_caption("Evolario")
from pygame.locals import *

flags = DOUBLEBUF
# Constants
PLAYER_RADIUS = 20
START_VEL = 3
FOOD_RADIUS = 5

TRANSPARENCY = 50
GRIDLINE_THICKNESS = 2
GRIDLINE_SPACING = 40
SCREEN = None
TIME_FONT = pygame.font.SysFont(None, 24)
SCORE_FONT = pygame.font.SysFont(None, 22)

# Make window start in center of screen
os.environ["SDL_VIDEO_CENTERED"] = "1"


# FUNCTIONS
def convert_time(t):
    """
    converts a time given in seconds to a time in
    minutes

    :param t: int
    :return: string
    """
    # t is time.time()
    t = round(t)
    seconds = t % 60
    minutes = t // 60
    if seconds < 10:
        seconds = "0" + str(seconds)
    return str(minutes) + ":" + str(seconds)


def draw_score(score):
    """
    draws each frame
    :return: None
    """

    # draw score
    text = TIME_FONT.render("Score: " + str(round(score)), 1, (0, 0, 0))
    SCREEN.blit(text, (10, 15 + text.get_height()))


def draw_scores(player_manager):
    players = player_manager.get_all()

    # Sort players by score in descending order
    sorted_players = sorted(
        players.values(), key=lambda player: player.score, reverse=True
    )

    # Define the title text
    title_text = TIME_FONT.render("Scoreboard", 1, (0, 0, 0))
    title_x = W - title_text.get_width() - 10
    SCREEN.blit(title_text, (title_x, 5))

    # Determine how many players to display (up to 3)
    max_players_to_display = min(len(sorted_players), 3)

    # Render and display the player scores
    start_y = 25
    for count, player in enumerate(sorted_players[:max_players_to_display]):
        player_rank = count + 1
        player_name = player.name
        score_text = SCORE_FONT.render(f"{player_rank}. {player_name}", 1, (0, 0, 0))
        text_x = title_x
        text_y = start_y + (count * 25)
        SCREEN.blit(score_text, (text_x, text_y))


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
    global SCREEN, W, H
    W = cfg.width
    H = cfg.height
    # setup pygame window
    SCREEN = pygame.display.set_mode((cfg.width, cfg.height), flags, 16)
    player_name = "Human"
    player_manager = PlayerManager(cfg)
    food_manager = FoodCellManager(cfg, player_manager)

    client = Client()
    _id = client.connect(player_name)
    response = client.send("get")
    try:
        food_manager.food_cells, player_manager.players = response
        print("[INFO]\tClient-side connected to server")
    except Exception:
        print("Error: Unexpected response from client.send('get')")
    clock = pygame.time.Clock()
    # Get current player
    font = pygame.font.Font(None, 36)
    run = True
    while run:
        player = player_manager.get(_id)
        # limit the game to 30 frames per second
        clock.tick_busy_loop(cfg.fps)

        # Calculate velocity based on score
        vel = max(START_VEL - round(player.score / 14), 1)
        player.update_speed(vel)

        # move player
        player.move()

        # create data to send to server
        data = "move " + str(player.get_x()) + " " + str(player.get_y())

        # Send new data to server
        client.send(data)

        data = "get"
        # Get current information from server
        response = client.send(data)
        food_manager.food_cells, player_manager.players = response

        for event in pygame.event.get():
            # if user hits red x button close window
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                # if user hits a escape key close program
                if event.key == pygame.K_ESCAPE:
                    run = False

        # Draw game window
        # Set background colour
        SCREEN.fill((255, 255, 255))
        draw_grid()
        food_manager.draw(SCREEN)
        player_manager.draw(SCREEN)
        draw_score(player.score)
        draw_scores(player_manager)
        fps = font.render(f"FPS: {clock.get_fps():.0f}", True, (0, 0, 0))
        fps = SCREEN.blit(fps, (10, 10))
        pygame.display.update()

    client.disconnect()
    pygame.quit()
    quit()


if __name__ == "__main__":
    main()
