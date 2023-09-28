# Where the player is x
# Where the player is y
# Food euclidean distances
# Where players are in the local vicinity of the player x
# Where players are in the local vicinity of the player y
import contextlib

import neat

from client import Client

with contextlib.redirect_stdout(None):
    import pygame

import math

PLAYER_RADIUS = 20
NUM_PLAYERS = 10
NUM_FOODS = 10
CONFIG_FILE = "config-feedforward.txt"
W, H = 1920, 1080


def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


def evaluate_genomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = evaluate_genome(genome, config)


# Used to evaluate a single bot
def evaluate_genome(genome, config):
    name = "testbot"
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    fitness = 0
    global players

    # start by connecting to the network
    client = Client()
    current_id = client.connect(name)
    foods, players, game_time = client.send("get")

    # Define an area of 20 radius around the player
    local_vicinity = 100
    # Create a list called foods_data to contain the euclidean distances of the foods
    foods_data = [
        calculate_distance(
            food[0], food[1], players[current_id]["x"], players[current_id]["y"]
        )
        for food in foods
        if calculate_distance(
            food[0], food[1], players[current_id]["x"], players[current_id]["y"]
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
    ]

    # There can only be 10 players in the local vicinity; if there are less than 10, fill the rest with 0s
    if len(players_data) < NUM_PLAYERS:
        players_data += [0] * (NUM_PLAYERS - len(players_data))
    else:
        players_data = players[:NUM_PLAYERS]

    if len(foods_data) < NUM_FOODS:
        foods_data += [0] * (NUM_FOODS - len(foods_data))
    else:
        foods_data = foods[:NUM_FOODS]

    # Create input data for the neural network
    input_data = (
        players[current_id]["x"],
        players[current_id]["y"],
        *foods_data,
        *players_data,
    )
    # setup the clock, limit to 30fps
    clock = pygame.time.Clock()

    run = True
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

    while run:
        clock.tick(60)
        player = players[current_id]
        vel = 3 - round(player["score"] / 14)
        if vel <= 1:
            vel = 1

        output = net.activate(input_data)

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

        x, y = players[current_id]["x"], players[current_id]["y"]
        data = f"move {x} {y}"
        # send data to server and recieve back all players information
        foods, players, game_time = client.send(data)


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
winner = population.run(evaluate_genomes, 1000)

# Test the AI's performance in the game
# test_ai(winner)
