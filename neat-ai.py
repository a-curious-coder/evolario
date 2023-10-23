import concurrent.futures
import contextlib
import math
import threading
import time

import hydra
import neat
import pygame
from omegaconf import DictConfig

from client.client import Client
from common.food import FoodCellManager
from common.player import PlayerManager
from common.utilities import calculate_distance
from user import draw_grid, draw_score, draw_scores

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


class NeatAI:
    """NEAT AI class"""

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.player_cfg = cfg.player
        self.food_cfg = cfg.food
        self.player_manager = PlayerManager(cfg)
        self.food_manager = FoodCellManager(cfg, self.player_manager)

        self.generations = 10

        self.neat_config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            cfg.neat_ai_config_file,
        )

        # Create the NEAT population
        self.population = neat.Population(self.neat_config)
        # Add reporters for output and statistics
        self.population.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        self.population.add_reporter(stats)

        self.nearby_player_limit = 10
        self.nearby_food_limit = 10
        self.generation_time_limit = 10
        self.start_next_generation = False

    def run(self):
        # Start a timer that will set should_restart to True after 60 seconds
        # self.timer = threading.Timer(
        #     self.generation_time_limit, self.start_next_generation
        # )
        # self.timer.start()
        self.winner = self.population.run(self.evaluate_genomes, self.generations)

    def evaluate_genomes(self, genomes, config):
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = {
                executor.submit(
                    self.evaluate_single_genome, genome_id, genome, config
                ): (
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
        # Restart server
        self.restart_server()
        print("[INFO]\tGeneration complete")

    # def evaluate_genomes(self, genomes, config):
    #     for genome_id, genome in genomes:
    #         genome.fitness = self.evaluate_single_genome(genome_id, genome, config)

    def evaluate_single_genome(self, genome_id, genome, config):
        name = f"bot_{genome_id}"
        net = neat.nn.FeedForwardNetwork.create(genome, config)

        # Metric weights
        score_weight = 0.5
        distance_weight = 0.2
        exploration_weight = 0.3

        # start by connecting to the network
        client = Client()
        current_id = client.connect(name)
        self.food_manager.food_cells, self.player_manager.players = client.send("get")
        # setup the clock, limit to 30fps
        clock = pygame.time.Clock()
        movement_threshold = 0.2  # Change this value according to your game's scale
        total_distance_travelled = 0
        last_position = (
            self.player_manager.players[current_id].position.x,
            self.player_manager.players[current_id].position.y,
        )
        start_time = time.time()
        last_move_time = time.time()
        while True:
            player = self.player_manager.players[current_id]
            distance_moved = 0
            time_since_last_move = time.time() - last_move_time

            clock.tick(self.cfg.fps)
            # print(
            #     f"{name} : {player.position.get()} : {player.score} : {time_since_last_move:.2f}"
            # )

            # Create a list called foods_data to contain the euclidean distances of the foods
            nearby_food_distances = self.get_nearby_food(current_id)
            nearby_player_distances = self.get_nearby_players(current_id)

            # Create input data for the neural network
            input_data = (
                self.player_manager.players[current_id].position.x,
                self.player_manager.players[current_id].position.y,
                *nearby_food_distances,
                *nearby_player_distances,
            )

            # Calculate the velocity of the player
            vel = (
                self.player_cfg.start_velocity
                - self.player_manager.players[current_id].score / 14
            )
            if vel <= self.player_cfg.min_velocity:
                vel = self.player_cfg.min_velocity

            # Get the output of the neural network
            output = net.activate(input_data)

            # Get the next move of the player
            self.player_manager.players[current_id] = self.get_next_move(
                output, self.player_manager.players[current_id], vel
            )

            # Create the next move command
            x, y = (
                self.player_manager.players[current_id].position.x,
                self.player_manager.players[current_id].position.y,
            )
            next_move = f"move {x} {y}"

            # send next_move to server and recieve back all players information
            self.food_manager.food_cells, self.player_manager.players = client.send(
                next_move
            )

            current_position = (
                self.player_manager.players[current_id].position.x,
                self.player_manager.players[current_id].position.y,
            )

            if current_position != last_position:
                distance_moved = calculate_distance(
                    current_position[0],
                    current_position[1],
                    *last_position,
                )

                if distance_moved > movement_threshold:
                    total_distance_travelled += distance_moved
                    last_position = current_position
                    last_move_time = time.time()

            if time_since_last_move >= 2.5 or self.start_next_generation:
                exploration_score = (time.time() - start_time) * exploration_weight
                distance_score = total_distance_travelled * distance_weight
                score_score = (
                    self.player_manager.players[current_id].score
                ) * score_weight
                fitness_score = (exploration_score + distance_score + score_score) / 100
                print(f"{name} : {fitness_score:.2f}")
                # You can return a default fitness score or a penalty
                return fitness_score

    def get_next_move(self, output, player, vel):
        """
        Gets the next move of the player based on the output of the neural network

        Parameters:
            output (list): The output of the neural network
            player (Player): The player instance whose next move is to be determined
            vel (int): The velocity of the player
        """
        max_index = output.index(max(output))
        x, y = player.position.x, player.position.y

        move_directions = {
            "left": (-vel, 0),
            "right": (vel, 0),
            "up": (0, -vel),
            "down": (0, vel),
            "up-left": (-vel, -vel),
            "up-right": (vel, -vel),
            "down-left": (-vel, vel),
            "down-right": (vel, vel),
        }

        move = move_directions.get(directions[max_index])

        if move:
            new_x = round(x + move[0])
            new_y = round(y + move[1])

            if (
                0 <= new_x - player.radius - player.score <= self.cfg.width
                and 0 <= new_y - player.radius - player.score <= self.cfg.height
            ):
                player.position.x = new_x
                player.position.y = new_y

        return player

    def get_nearby_players(self, current_id):
        nearby_player_distances = []
        current_player = self.player_manager.players[current_id]

        for player_id, player in self.player_manager.players.items():
            if player_id == current_id:
                continue

            distance = calculate_distance(
                player.position.x,
                player.position.y,
                current_player.position.x,
                current_player.position.y,
            )

            if distance < 100:
                # Normalize the distance and append to the list
                nearby_player_distances.append(distance / 100)

        # Fill the rest with 0s if there are less than 10 players
        num_players = len(nearby_player_distances)
        if num_players < self.nearby_player_limit:
            nearby_player_distances.extend(
                [0] * (self.nearby_player_limit - num_players)
            )

        return nearby_player_distances[: self.nearby_player_limit]

    def get_nearby_food(self, current_id):
        current_player = self.player_manager.players[current_id]
        nearby_food_distances = []

        for food_cell in self.food_manager.food_cells:
            distance = calculate_distance(
                current_player.position.x,
                current_player.position.y,
                food_cell.position.x,
                food_cell.position.y,
            )

            if distance < 100:
                normalized_distance = distance / 100
                nearby_food_distances.append(normalized_distance)

        if len(nearby_food_distances) < self.nearby_food_limit:
            remaining_length = self.nearby_food_limit - len(nearby_food_distances)
            nearby_food_distances.extend([0] * remaining_length)
        else:
            nearby_food_distances = nearby_food_distances[: self.nearby_food_limit]

        return nearby_food_distances

    def restart_server(self):
        client = Client()
        client.connect("controller")
        client.send("restart")
        client.disconnect()


def preview_game(cfg: DictConfig):
    global SCREEN, W, H
    W = cfg.width
    H = cfg.height
    # setup pygame window
    SCREEN = pygame.display.set_mode((cfg.width, cfg.height), 1, 16)
    player_name = "spectator"
    player_manager = PlayerManager(cfg)
    food_manager = FoodCellManager(cfg, player_manager)

    client = Client()
    _ = client.connect(player_name)
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
        # limit the game to 30 frames per second
        clock.tick_busy_loop(cfg.fps)

        # Get current information from server
        response = client.send("get")
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
        draw_grid(SCREEN, cfg)
        food_manager.draw(SCREEN)
        player_manager.draw(SCREEN)
        draw_score(SCREEN, player_manager.get_top_score())
        draw_scores(SCREEN, cfg, player_manager)
        fps = font.render(f"FPS: {clock.get_fps():.0f}", True, (0, 0, 0))
        fps = SCREEN.blit(fps, (10, 10))
        pygame.display.update()

    client.disconnect()
    pygame.quit()
    quit()


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    # Run preview game in a separate thread
    with contextlib.suppress(Exception):
        threading.Thread(target=preview_game, args=(cfg,)).start()
    # neat_ai = NeatAI(cfg)
    # neat_ai.run()


if __name__ == "__main__":
    main()
