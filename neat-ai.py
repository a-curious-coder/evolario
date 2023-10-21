# Where the player is x
# Where the player is y
# Food euclidean distances
# Where players are in the local vicinity of the player x
# Where players are in the local vicinity of the player y
import concurrent.futures
import contextlib
import threading
import time
import traceback

import neat

from client.client import Client

with contextlib.redirect_stdout(None):
    import pygame

import math

GENERATION_TIMER = 15
PLAYER_RADIUS = 20
NUM_PLAYERS = 10
NUM_FOODS = 10
CONFIG_FILE = "config-feedforward.txt"
W, H = 1920, 1080
FROZEN_PLAYERS = [NUM_PLAYERS * False]
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
    """
    Calculates the distance between two points in 2D space

    Parameters:
        x1 (int): The x-coordinate of the first point.
        y1 (int): The y-coordinate of the first point.
        x2 (int): The x-coordinate of the second point.
        y2 (int): The y-coordinate of the second point.
    """
    return math.hypot(x2 - x1, y2 - y1)


def evaluate_genomes(genomes, config):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
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
    print("[INFO]\tGeneration complete")


# def evaluate_genomes(genomes, config):
#     for genome_id, genome in genomes:
#         try:
#             genome.fitness = evaluate_single_genome(genome_id, genome, config)
#         except Exception as e:
#             print(f"[INFO]\tAn error occurred while evaluating genome {genome_id}: {e}")
#             traceback.print_exc()
#     print("[INFO]\tGeneration complete")


# Used to evaluate a single bot
def evaluate_single_genome(genome_id, genome, config):
    global should_restart
    name = f"bot_{genome_id}"
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    global players

    # start by connecting to the network
    client = Client()
    current_id = client.connect(name)
    food_cells, players = client.send("get")

    # setup the clock, limit to 30fps
    clock = pygame.time.Clock()
    game_running = True
    movement_threshold = 4.9  # Change this value according to your game's scale
    total_distance_travelled = 0
    last_position = (players[current_id].position.x, players[current_id].position.y)
    while game_running:
        distance_moved = 0
        last_move_time = time.time()
        clock.tick(20)
        # Define an area of 20 radius around the player
        local_vicinity = 100
        # Create a list called foods_data to contain the euclidean distances of the foods
        food_data = [
            calculate_distance(
                players[current_id].position.x,
                players[current_id].position.y,
                food_cell.position.x,
                food_cell.position.y,
            )
            for food_cell in food_cells
            if calculate_distance(
                players[current_id].position.x,
                players[current_id].position.y,
                food_cell.position.x,
                food_cell.position.y,
            )
            < local_vicinity
        ]

        players_data = [
            calculate_distance(
                players[player].position.x,
                players[player].position.y,
                players[current_id].position.x,
                players[current_id].position.y,
            )
            for player in players
            if calculate_distance(
                players[player].position.x,
                players[player].position.y,
                players[current_id].position.x,
                players[current_id].position.y,
            )
            < local_vicinity
            and player != current_id
        ]

        # There can only be 10 players in the local vicinity; if there are less than 10, fill the rest with 0s
        if len(players_data) < NUM_PLAYERS:
            players_data += [0] * (NUM_PLAYERS - len(players_data))
        else:
            players_data = players_data[:NUM_PLAYERS]

        # Considering the local vicinity, normalize the data
        for i in range(len(players_data)):
            players_data[i] = players_data[i] / local_vicinity

        if len(food_data) < NUM_FOODS:
            food_data += [0] * (NUM_FOODS - len(food_data))
        else:
            food_data = food_data[:NUM_FOODS]

        for i in range(len(food_data)):
            food_data[i] = food_data[i] / local_vicinity

        # Create input data for the neural network
        input_data = (
            players[current_id].position.x,
            players[current_id].position.y,
            *food_data,
            *players_data,
        )

        vel = 5 - round(players[current_id].score / 14)
        if vel <= 1:
            vel = 1

        output = net.activate(input_data)

        players[current_id] = get_next_move(output, players[current_id], vel)

        x, y = players[current_id].position.x, players[current_id].position.y
        next_move = f"move {x} {y}"
        # send next_move to server and recieve back all players information
        food_cells, players = client.send(next_move)

        if (
            players[current_id].position.x,
            players[current_id].position.y,
        ) != last_position:
            distance_moved += calculate_distance(
                players[current_id].position.x,
                players[current_id].position.y,
                *last_position,
            )

            if distance_moved > movement_threshold:
                total_distance_travelled += distance_moved
                last_position = (
                    players[current_id].position.x,
                    players[current_id].position.y,
                )
                last_move_time = time.time()
        else:
            pass

        if time.time() - last_move_time >= 5 or should_restart:
            print(f"{name} : {total_distance_travelled} : {players[current_id].score}")
            # You can return a default fitness score or a penalty
            return (players[current_id].score / 100) + (total_distance_travelled / 100)


def get_next_move(output, player, vel):
    # movement based on key presses
    if directions[output.index(max(output))] == "left":
        if player.position.x - vel - PLAYER_RADIUS - player.score >= 0:
            player.position.x = player.position.x - vel

    if directions[output.index(max(output))] == "right":
        if player.position.x + vel + PLAYER_RADIUS + player.score <= W:
            player.position.x = player.position.x + vel

    if directions[output.index(max(output))] == "up":
        if player.position.y - vel - PLAYER_RADIUS - player.score >= 0:
            player.position.y = player.position.y - vel

    if directions[output.index(max(output))] == "down":
        if player.position.y + vel + PLAYER_RADIUS + player.score <= H:
            player.position.y = player.position.y + vel

    if directions[output.index(max(output))] == "up-left":
        if (
            player.position.x - vel - PLAYER_RADIUS - player.score >= 0
            and player.position.y - vel - PLAYER_RADIUS - player.score >= 0
        ):
            player.position.x = player.position.x - vel
            player.position.y = player.position.y - vel

    if directions[output.index(max(output))] == "up-right":
        if (
            player.position.x + vel + PLAYER_RADIUS + player.score <= W
            and player.position.y - vel - PLAYER_RADIUS - player.score >= 0
        ):
            player.position.x = player.position.x + vel
            player.position.y = player.position.y - vel

    if directions[output.index(max(output))] == "down-left":
        if (
            player.position.x - vel - PLAYER_RADIUS - player.score >= 0
            and player.position.y + vel + PLAYER_RADIUS + player.score <= H
        ):
            player.position.x = player.position.x - vel
            player.position.y = player.position.y + vel

    if directions[output.index(max(output))] == "down-right":
        if (
            player.position.x + vel + PLAYER_RADIUS + player.score <= W
            and player.position.y + vel + PLAYER_RADIUS + player.score <= H
        ):
            player.position.x = player.position.x + vel
            player.position.y = player.position.y + vel

    if directions[output.index(max(output))] == "no movement":
        pass

    return player


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
winner = population.run(evaluate_genomes, 10)

# Test the AI's performance in the game
# test_ai(winner)
