import logging
import math
import os
import random
import socket
import sys
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
        self.start_time = 0

    def player_food_collision(self):
        """
        checks if any of the player have collided with any of the food

        :param players: a dictonary of players
        :param food: a list of food
        :return: None
        """
        try:
            for player in self.p_manager.players:
                p = self.p_manager.players[player]
                for i, cell in enumerate(self.f_manager.food_cells):
                    x = p.position.x - cell.position.x
                    y = p.position.y - cell.position.y
                    dis = math.sqrt(x**2 + y**2)
                    if dis <= self.cfg.player.radius + p.score:
                        self.p_manager.players[player].score += 1
                        self.f_manager.remove(i)
        except Exception as e:
            print(e)
            input("player_food_collision...")

    # def player_collisions(self):
    #     """
    #     checks for player collision and handles that collision

    #     :param players: dict
    #     :return: None
    #     """
    #     players = self.p_manager.get_all()  # Returns a dict of all player objects
    #     try:
    #         if len(players) > 1:
    #             for player1_key in players:
    #                 for player2_key in players:
    #                     if (
    #                         player1_key != player2_key
    #                     ):  # Make sure we're not comparing a player to itself
    #                         player1 = players[player1_key]
    #                         player2 = players[player2_key]

    #                         p1x = player1.position.x
    #                         p1y = player1.position.y

    #                         p2x = player2.position.x
    #                         p2y = player2.position.y

    #                         dis = math.sqrt((p1x - p2x) ** 2 + (p1y - p2y) ** 2)
    #                         if dis < player2.score - player1.score * 0.85:
    #                             self.p_manager.players[player2_key].score = math.sqrt(
    #                                 player2.score**2 + player1.score**2
    #                             )  # adding areas instead of radii
    #                             self.p_manager.players[player1_key].score = 0
    #                             (
    #                                 self.p_manager.players[player1_key].position.x,
    #                                 self.p_manager.players[player1_key].position.y,
    #                             ) = self.p_manager._get_start_location()
    #                             print(
    #                                 f"[GAME] "
    #                                 + self.p_manager.players[player2_key].name
    #                                 + " ATE "
    #                                 + self.p_manager.players[player1_key].name
    #                             )
    #     except Exception as e:
    #         print(e)
    #         input("player_player_collision...")

    def player_collisions(self):
        """
        checks for player collision and handles that collision

        :param players: dict
        :return: None
        """
        try:
            players = self.p_manager.get_all()  # Returns a dict of all player objects
            if len(players) > 1:
                # Create a tree from the player positions
                tree = cKDTree(
                    [
                        (player.position.x, player.position.y)
                        for player in players.values()
                    ]
                )

                for player1_key in players:
                    # Find all players close to player1
                    close_players = tree.query_ball_point(
                        [
                            players[player1_key].position.x,
                            players[player1_key].position.y,
                        ],
                        0.85,
                    )
                    for player2_key in close_players:
                        if (
                            player1_key != player2_key
                        ):  # Make sure we're not comparing a player to itself
                            player1 = players[player1_key]
                            player2 = players[player2_key]

                            dis = math.sqrt(
                                (player1.position.x - player2.position.x) ** 2
                                + (player1.position.y - player2.position.y) ** 2
                            )
                            if dis < player2.score - player1.score * 0.85:
                                self.p_manager.players[player2_key].score = math.sqrt(
                                    player2.score**2 + player1.score**2
                                )  # adding areas instead of radii
                                self.p_manager.players[player1_key].score = 0
                                (
                                    self.p_manager.players[player1_key].position.x,
                                    self.p_manager.players[player1_key].position.y,
                                ) = self.p_manager._get_start_location()
                                print(
                                    f"[GAME] "
                                    + self.p_manager.players[player2_key].name
                                    + " ATE "
                                    + self.p_manager.players[player1_key].name
                                )
        except Exception as e:
            print(e)
            input("player_player_collision...")

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
                    position = random_position(self.cfg.server.w, self.cfg.server.h)
                    for player in self.p_manager.players.values():
                        dis = math.sqrt(
                            (position.x - player.position.x) ** 2
                            + (position.y - player.position.y) ** 2
                        )
                        if dis <= self.cfg.player.radius + player.score:
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
            if addr[0] == self.server_config.hostname and not self.start:
                self.start = True
                self.start_time = time.time()
                print("[INFO] Game Started")

            self.connections += 1
            start_new_thread(self.threaded_client, args=(clientsocket, self._id))
            # self.threaded_client(clientsocket, self._id)
            self._id += 1

        print("[SERVER] Server offline")

    def threaded_client(self, clientsocket, _id):
        """
        Runs in a new thread for each player connected to the server

        :param con: ip address of connection
        :param _id: int
        :return: None
        """
        player_id = _id

        # Receive a name from the client
        name = clientsocket.recv(16).decode("utf-8")

        print(f"[INFO] {name}\tconnected")

        # Setup properties for each new player
        self.p_manager.add(player_id, name)

        # pickle data and send initial info to clients
        clientsocket.send(str.encode(str(player_id)))
        self.start = True
        while True:
            if self.start:
                game_time = round(time.time() - self.start_time)
                # if the game time passes the round time the game will stop
                if game_time >= self.server_config.round_time:
                    self.start = False

            try:
                # Receive data from client
                data = clientsocket.recv(self.server_config.buffer_size)

                if not data:
                    continue

                data = data.decode("utf-8")

                if data.split(" ")[0] == "move":
                    self.p_manager.handle_move_command(data, player_id)

                    # self.server_logic.player_food_collision()
                    # self.server_logic.player_collisions()

                    # if the amount of food is less than 150 create more
                    if len(self.f_manager.food_cells) <= self.cfg.food_quantity:
                        self.server_logic.create_food(1)
                elif data.split(" ")[0] == "get":
                    pass
                data_to_send = (self.f_manager.food_cells, self.p_manager.players)
                send_data = pickle.dumps(data_to_send)
                clientsocket.send(send_data)

            except Exception as e:
                print(f"[ERR]\t{e}")
                break  # if an exception has been reached disconnect client

            time.sleep(0.01)

        # When user disconnects
        print(f"[INFO] {name}\tdisconnected")

        self.connections -= 1
        # remove client information from players list
        self.p_manager.remove(player_id)
        clientsocket.close()  # close connection


# Set up a basic logger
logging.basicConfig(level=logging.INFO)


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    server = Server(cfg)
    server.start_server()


import cProfile

if __name__ == "__main__":
    cProfile.run("main()")
