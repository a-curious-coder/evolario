import contextlib

with contextlib.redirect_stdout(None):
    import pygame

import os

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

COLORS = [
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


# Dynamic Variables
players = {}
foods = []


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


def redraw_window(players, foods, game_time, score):
    """
    draws each frame
    :return: None
    """
    # Set background color
    SCREEN.fill((255, 255, 255))

    draw_grid()
    draw_foods(foods)
    draw_players()
    # Draw a line between the center of the player and the closest food to the player
    # for player in players:
    #     p = players[player]
    #     if len(foods) > 0:
    #         closest_food = foods[0]
    #         for food in foods:
    #             if abs(food[0] - p["x"]) + abs(food[1] - p["y"]) < abs(
    #                 closest_food[0] - p["x"]
    #             ) + abs(closest_food[1] - p["y"]):
    #                 closest_food = food
    #         pygame.draw.line(
    #             SCREEN,
    #             (0, 255, 0),
    #             (p["x"], p["y"]),
    #             (closest_food[0], closest_food[1]),
    #             1,
    #         )
    # Draw circle of player's local vicinity
    # for player in players:
    #     p = players[player]
    #     pygame.draw.circle(
    #         SCREEN,
    #         (0, 0, 0),
    #         (p["x"], p["y"]),
    #         PLAYER_RADIUS + round(p["score"]) + 100,
    #         1,
    #     )
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
            SCREEN.blit(text, (x, start_y + 1 * 25))
        else:
            SCREEN.blit(text, (x, start_y + count * 25))

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


def draw_foods(foods):
    # draw all the orbs/foods
    for food in foods:
        pygame.draw.circle(SCREEN, food[2], (food[0], food[1]), FOOD_RADIUS)


def draw_players():
    # draw each player in the list
    for player in sorted(players, key=lambda x: players[x]["score"]):
        p = players[player]
        pygame.draw.circle(
            SCREEN, p["color"], (p["x"], p["y"]), PLAYER_RADIUS + round(p["score"])
        )
        # Draw border around player
        pygame.draw.circle(
            SCREEN,
            (0, 0, 0),
            (p["x"], p["y"]),
            PLAYER_RADIUS + round(p["score"]),
            2,
        )
        # render and draw name for each player
        text = NAME_FONT.render(p["name"], 1, (0, 0, 0))
        SCREEN.blit(
            text, (p["x"] - text.get_width() / 2, p["y"] - text.get_height() / 2)
        )


class Player:
    def __init__(self, name, x, y, score, color):
        self.name = name
        self.x = x
        self.y = y
        self.score = score
        self.color = color


class PlayerManager:
    def __init__(self):
        self.players = {}

    def add_player(self, name, x, y, score, color):
        self.players[name] = Player(name, x, y, score, color)

    def update_player(self, name, x, y, score, color):
        self.players[name].x = x
        self.players[name].y = y
        self.players[name].score = score
        self.players[name].color = color

    def remove_player(self, name):
        del self.players[name]

    def get_players(self):
        return self.players

    def draw_players(self):
        for player in self.players:
            p = self.players[player]
            pygame.draw.circle(
                SCREEN, p.color, (p.x, p.y), PLAYER_RADIUS + round(p.score)
            )
            # Draw border around player
            pygame.draw.circle(
                SCREEN,
                (0, 0, 0),
                (p.x, p.y),
                PLAYER_RADIUS + round(p.score),
                2,
            )
            # render and draw name for each player
            text = NAME_FONT.render(p.name, 1, (0, 0, 0))
            SCREEN.blit(text, (p.x - text.get_width() / 2, p.y - text.get_height() / 2))


def main(player_name):
    """
    function for running the game,
    includes the main loop of the game

    :param players: a list of dicts represting a player
    :return: None
    """
    global players

    # start by connecting to the network
    client = Client()
    current_id = client.connect(player_name)
    foods, players, game_time = client.send("get")

    # setup the clock, limit to 30fps
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(60)  # 30 fps max
        player = players[current_id]
        vel = START_VEL - round(player["score"] / 14)
        if vel <= 1:
            vel = 1

        # get key presses
        keys = pygame.key.get_pressed()

        data = ""
        # movement based on key presses
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if player["x"] - vel - PLAYER_RADIUS - player["score"] >= 0:
                player["x"] = player["x"] - vel

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if player["x"] + vel + PLAYER_RADIUS + player["score"] <= W:
                player["x"] = player["x"] + vel

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if player["y"] - vel - PLAYER_RADIUS - player["score"] >= 0:
                player["y"] = player["y"] - vel

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if player["y"] + vel + PLAYER_RADIUS + player["score"] <= H:
                player["y"] = player["y"] + vel

        data = "move " + str(player["x"]) + " " + str(player["y"])

        # send data to server and recieve back all players information
        foods, players, game_time = client.send(data)

        for event in pygame.event.get():
            # if user hits red x button close window
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                # if user hits a escape key close program
                if event.key == pygame.K_ESCAPE:
                    run = False

        # redraw window then update the frame
        redraw_window(players, foods, game_time, player["score"])
        pygame.display.update()

    client.disconnect()
    pygame.quit()
    quit()


try:
    # start game
    main("Human")
except KeyboardInterrupt as k:
    print("Keyboard Interrupt")
