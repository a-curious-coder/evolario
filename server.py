import math
import socket
import threading
import time
from _thread import start_new_thread

import _pickle as pickle
import hydra
from omegaconf import DictConfig
from scipy.spatial import cKDTree

from common.food import FoodCellManager
from common.player import PlayerManager
from common.utilities import random_position


class ServerConfig:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.port = self.cfg.server.port
        self.buffer_size = self.cfg.server.buffer_size
        self.round_time = self.cfg.server.round_time * 1000
        self.w = self.cfg.server.w
        self.h = self.cfg.server.h
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


class ServerLogic:
    def __init__(
        self, cfg: DictConfig, p_manager: PlayerManager, f_manager: FoodCellManager
    ):
        self.cfg = cfg
        self.p_manager = p_manager
        self.f_manager = f_manager
        self.start = False
        self.start_time = time.time()

    def player_food_collision(self):
        """
        checks if any of the player have collided with any of the food

        :param players: a dictionary of players
        :param food: a list of food
        :return: None
        """
        try:
            # Build a k-d tree of food cell positions and a dictionary for fast removal
            food_positions = [cell.xy for cell in self.f_manager.food_cells]
            food_tree = cKDTree(food_positions)
            food_dict = {i: cell for i, cell in enumerate(self.f_manager.food_cells)}

            for player, p in self.p_manager.players.items():
                player_radius = self.cfg.player.radius + p.score
                # Find food cells within player_radius of the player
                indices = food_tree.query_ball_point(
                    (p.position.x, p.position.y), player_radius
                )
                for index in indices:
                    cell = food_dict.pop(
                        index, None
                    )  # Remove the food cell from the dictionary
                    if cell is not None:
                        self.p_manager.players[player].score += 1
                        # Remove the food cell from the original list as well
                        self.f_manager.food_cells.remove(cell)

        except Exception as e:
            print(e)

    def player_collisions(self):
        """
        checks if any of the players have collided with each other

        :param players: a dictionary of players
        :return: None
        """
        try:
            # Build a k-d tree of player positions and a dictionary for fast removal
            player_positions = [
                p.position.get() for p in self.p_manager.players.values()
            ]
            player_tree = cKDTree(player_positions)
            player_dict = {
                player_id: player
                for player_id, player in self.p_manager.players.items()
            }

            for player_id, player in self.p_manager.players.items():
                player_radius = player.get_radius()
                # Find players within player_radius of the current player
                indices = player_tree.query_ball_point(
                    (player.position.x, player.position.y), player_radius
                )
                for other_player_id in indices:
                    if other_player_id != player_id:
                        other_player = player_dict.get(other_player_id)
                        if other_player:
                            # Handle the collision between players here
                            self.handle_player_collision(player_id, other_player_id)
                            break

        except Exception as e:
            print(e)

    def handle_player_collision(self, player1_id, player2_id):
        """Handles the collision between two players

        :param player1: The first player
        :param player2: The second player
        """
        self.p_manager.players[player1_id].score += (
            self.p_manager.players[player2_id].score // 2
        )
        # Deal with player 2
        self.p_manager.players[player2_id].eaten = True
        self.p_manager.players[player2_id].score = 0
        print(
            f"[GAME] {self.p_manager.players[player1_id].score.name} ATE {self.p_manager.players[player2_id].score.name}"
        )

    def create_food(self, n):
        """
        Create food cells on the map

        :param food: existing list of food cells
        :param n: the number of food cells to create
        """
        try:
            for _ in range(n):
                while True:
                    stop = True
                    position = random_position(self.cfg.width, self.cfg.height)
                    for player in self.p_manager.players.values():
                        dis = math.hypot(
                            position.x - player.position.x,
                            position.y - player.position.y,
                        )
                        if dis <= player.get_radius():
                            stop = False
                    if stop:
                        break

                self.f_manager.add(position)
        except Exception as e:
            print(e)
            input("create_food...")


class Server:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.p_manager = PlayerManager(cfg)
        self.f_manager = FoodCellManager(cfg, self.p_manager)
        self.server_config = ServerConfig(cfg)
        self.server_logic = ServerLogic(cfg, self.p_manager, self.f_manager)
        self.connections = 0
        self._id = 0
        self.game_time = "Starting Soon"
        self.start = False
        self.start_time = 0

    def bind_server(self):
        try:
            self.server_config.socket.bind(
                (self.server_config.hostname, self.server_config.port)
            )
        except socket.error as e:
            print(str(e))
            print("[SERVER] Server could not start")
            quit()

    def listen_for_connections(self):
        self.server_config.socket.listen()
        print(f"[SERVER] Local ip {self.server_config.ip}")

    def save_ip(self):
        with open("ip.txt", "w", encoding="utf-8") as file:
            file.write(self.server_config.ip)

    def start_server(self):
        self.bind_server()
        self.listen_for_connections()
        self.save_ip()

        print("[SERVER] Waiting for connections")
        print("[INFO] Setting up level")
        self.server_logic.create_food(self.cfg.food_quantity)

        # Keep looping to accept new connections
        while True:
            clientsocket, addr = self.server_config.socket.accept()
            if addr[0] == self.server_config.ip and not self.start:
                self.start = True
                self.start_time = time.time()
                print("[INFO] Game Started")

            self.connections += 1
            start_new_thread(self.threaded_client, (clientsocket, self._id))
            # self.threaded_client(clientsocket, self._id)
            self._id += 1

        print("[SERVER] Server offline")

    def restart_game(self):
        self.p_manager = PlayerManager(self.cfg)
        self.f_manager = FoodCellManager(self.cfg, self.p_manager)
        self.server_logic = ServerLogic(self.cfg, self.p_manager, self.f_manager)
        self.connections = 0
        self._id = 0
        self.game_time = "Starting Soon"
        self.start = False
        self.start_time = 0
        self.server_logic.create_food(self.cfg.food_quantity)

    def threaded_client(self, clientsocket, _id):
        """
        Runs in a new thread for each player connected to the server

        :param con: ip address of connection
        :param _id: int
        :return: None
        """
        try:
            player_id = _id

            # Receive a name from the client
            name = clientsocket.recv(16).decode("utf-8")

            print(f"[INFO] {name} connected")
            if name != "controller" and name != "spectator":
                # Setup properties for each new player
                self.p_manager.add(player_id, name)

                # pickle data and send initial info to clients
                clientsocket.send(str.encode(str(player_id)))
                self.start = True

            # Create a separate thread for receiving data from the client
            recv_thread = threading.Thread(
                target=self.receive_data, args=(clientsocket, player_id, name)
            )
            recv_thread.start()
            while True:
                if self.start:
                    game_time = round(time.time() - self.start_time)
                    # if the game time passes the round time the game will stop
                    if game_time >= self.server_config.round_time:
                        self.start = False

                time.sleep(0.001)

        except Exception as e:
            print(f"[ERR]\t{e}")

    # def update_game(self):
    #     while True:
    #         (self.f_manager, self.p_manager) = self.collision_thread.get_game_elements()

    def receive_data(self, clientsocket, player_id, name):
        """
        Receives data from the client and sends data to the client

        :param socket clientsocket: socket object
        :param int player_id: id of the player
        """
        while True:
            try:
                # Receive data from client
                data = clientsocket.recv(self.server_config.buffer_size)

                if not data:
                    break

                data = data.decode("utf-8")
                if data.split(" ")[0] == "restart":
                    self.restart_game()
                if data.split(" ")[0] == "move":
                    self.p_manager.handle_move_command(data, player_id)

                    self.server_logic.player_food_collision()
                    self.server_logic.player_collisions()

                    # if the amount of food is less than 150 create more
                    if len(self.f_manager.food_cells) <= self.cfg.food_quantity:
                        self.server_logic.create_food(1)
                data_to_send = (self.f_manager.food_cells, self.p_manager.players)
                send_data = pickle.dumps(data_to_send)
                clientsocket.send(send_data)

            except Exception as e:
                print(f"[ERR]\tDisconnected {e}")
                break  # if an exception has been reached disconnect client
        # When user disconnects
        print(f"[INFO] {name}\tdisconnected")

        self.connections -= 1
        # remove client information from players list
        self.p_manager.remove(player_id)
        # Close the connection using a context manager
        clientsocket.close()


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    server = Server(cfg)
    server.start_server()


import cProfile

if __name__ == "__main__":
    cProfile.run("main()")
