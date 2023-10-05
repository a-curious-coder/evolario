# Where the player is x
# Where the player is y
# Food euclidean distances
# Where players are in the local vicinity of the player x
# Where players are in the local vicinity of the player y
import concurrent.futures
import contextlib
import threading
import time

import neat

from client import Client

with contextlib.redirect_stdout(None):
    import pygame

import math

GENERATION_TIMER = 15
PLAYER_RADIUS = 20
NUM_PLAYERS = 10
NUM_FOODS = 10
CONFIG_FILE = "config-feedforward.txt"
W, H = 1920, 1080

directions = [
    "up",
    "down",
    "left",
    "right",
    "up-left",
    "up-right",
    "down-left",
    "down-right",
    "no movement",
]

# This flag is checked in your evaluation function
should_restart = False


def restart_generation():
    global should_restart
    should_restart = True


# Start a timer that will set should_restart to True after 60 seconds
timer = threading.Timer(GENERATION_TIMER, restart_generation)
timer.start()


def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


def evaluate_genomes(genomes, config):
    global should_restart
    threads = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(evaluate_single_genome, genome_id, genome, config): (
                genome_id,
                genome,
            )
            for genome_id, genome in genomes
        }
        for future in concurrent.futures.as_completed(futures):
            genome_id, genome = futures[future]
            try:
                genome.fitness = future.result()
            except Exception as e:
                print(
                    f"[INFO]\tAn error occurred while evaluating genome {genome_id}: {e}"
                )
    # Reset the flag for the next generation
    should_restart = False
    # Restart the timer for the next generation
    timer = threading.Timer(GENERATION_TIMER, restart_generation)
    timer.start()
    print("[INFO]\tGeneration complete")


# Used to evaluate a single bot
def evaluate_single_genome(genome_id, genome, config):
    global should_restart
    name = f"bot_{genome_id}"
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    global players

    # start by connecting to the network
    client = Client()
    current_id = client.connect(name)
    foods, players, game_time = client.send("get")

    # setup the clock, limit to 30fps
    clock = pygame.time.Clock()

    game_running = True

    while game_running:
        clock.tick(60)
        # Define an area of 20 radius around the player
        local_vicinity = 100
        # Create a list called foods_data to contain the euclidean distances of the foods
        foods_data = [
            calculate_distance(
                players[current_id]["x"], players[current_id]["y"], food[0], food[1]
            )
            for food in foods
            if calculate_distance(
                players[current_id]["x"], players[current_id]["y"], food[0], food[1]
            )
            < local_vicinity
        ]

        players_data = [
            calculate_distance(
                players[player]["x"],
                players[player]["y"],
                players[current_id]["x"],
                players[current_id]["y"],
            )
            for player in players
            if calculate_distance(
                players[player]["x"],
                players[player]["y"],
                players[current_id]["x"],
                players[current_id]["y"],
            )
            < local_vicinity
            and player != current_id
        ]

        # There can only be 10 players in the local vicinity; if there are less than 10, fill the rest with 0s
        if len(players_data) < NUM_PLAYERS:
            players_data += [0] * (NUM_PLAYERS - len(players_data))
        else:
            players_data = players_data[:NUM_PLAYERS]

        if len(foods_data) < NUM_FOODS:
            foods_data += [0] * (NUM_FOODS - len(foods_data))
        else:
            foods_data = foods_data[:NUM_FOODS]

        # Create input data for the neural network
        input_data = (
            players[current_id]["x"],
            players[current_id]["y"],
            *foods_data,
            *players_data,
        )

        player = players[current_id]
        vel = 3 - round(player["score"] / 14)
        if vel <= 1:
            vel = 1

        output = net.activate(input_data)

        player = get_next_move(output, player, vel)

        x, y = players[current_id]["x"], players[current_id]["y"]
        data = f"move {x} {y}"
        # send data to server and recieve back all players information
        foods, players, game_time = client.send(data)
        if should_restart:
            # You can return a default fitness score or a penalty
            return players[current_id]["score"]


def get_next_move(output, player, vel):
    # movement based on key presses
    if directions[output.index(max(output))] == "left":
        if player["x"] - vel - PLAYER_RADIUS - player["score"] >= 0:
            player["x"] = player["x"] - vel

    if directions[output.index(max(output))] == "right":
        if player["x"] + vel + PLAYER_RADIUS + player["score"] <= W:
            player["x"] = player["x"] + vel

    if directions[output.index(max(output))] == "up":
        if player["y"] - vel - PLAYER_RADIUS - player["score"] >= 0:
            player["y"] = player["y"] - vel

    if directions[output.index(max(output))] == "down":
        if player["y"] + vel + PLAYER_RADIUS + player["score"] <= H:
            player["y"] = player["y"] + vel

    if directions[output.index(max(output))] == "up-left":
        if (
            player["x"] - vel - PLAYER_RADIUS - player["score"] >= 0
            and player["y"] - vel - PLAYER_RADIUS - player["score"] >= 0
        ):
            player["x"] = player["x"] - vel
            player["y"] = player["y"] - vel

    if directions[output.index(max(output))] == "up-right":
        if (
            player["x"] + vel + PLAYER_RADIUS + player["score"] <= W
            and player["y"] - vel - PLAYER_RADIUS - player["score"] >= 0
        ):
            player["x"] = player["x"] + vel
            player["y"] = player["y"] - vel

    if directions[output.index(max(output))] == "down-left":
        if (
            player["x"] - vel - PLAYER_RADIUS - player["score"] >= 0
            and player["y"] + vel + PLAYER_RADIUS + player["score"] <= H
        ):
            player["x"] = player["x"] - vel
            player["y"] = player["y"] + vel

    if directions[output.index(max(output))] == "down-right":
        if (
            player["x"] + vel + PLAYER_RADIUS + player["score"] <= W
            and player["y"] + vel + PLAYER_RADIUS + player["score"] <= H
        ):
            player["x"] = player["x"] + vel
            player["y"] = player["y"] + vel

    if directions[output.index(max(output))] == "no movement":
        pass


# Set up the NEAT configuration
config = neat.Config(
    neat.DefaultGenome,
    neat.DefaultReproduction,
    neat.DefaultSpeciesSet,
    neat.DefaultStagnation,
    CONFIG_FILE,
)

# Create the NEAT population
population = neat.Population(config)

# Add reporters for output and statistics
population.add_reporter(neat.StdOutReporter(True))
stats = neat.StatisticsReporter()
population.add_reporter(stats)

# Run the training for a certain number of generations
winner = population.run(evaluate_genomes, 25)

# Test the AI's performance in the game
# test_ai(winner)
