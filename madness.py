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
        for player in self.p_manager.players:
            p = self.p_manager.players[player]
            for cell in self.f_manager.food_cells:
                f = self.f_manager.food_cells[cell]

                dis = math.sqrt(
                    (p.position.x - f.position.x) ** 2
                    + (p.position.y - f.position.y) ** 2
                )
                if dis <= self.cfg.player.player_radius + p.score:
                    self.p_manager.players[player].score += 1
                    self.f_manager.remove(cell)

    def player_collisions(self):
        """
        checks for player collision and handles that collision

        :param players: dict
        :return: None
        """
        sort_players = sorted(
            self.p_manager.players, key=lambda x: self.p_manager.players[x].score
        )
        for x, player1 in enumerate(sort_players):
            for player2 in sort_players[x + 1 :]:
                p1x = self.p_manager.players[player1].position.x
                p1y = self.p_manager.players[player1].position.y

                p2x = self.p_manager.players[player2].position.x
                p2y = self.p_manager.players[player2].position.y

                dis = math.sqrt((p1x - p2x) ** 2 + (p1y - p2y) ** 2)
                if (
                    dis
                    < self.p_manager.players[player2].score
                    - self.p_manager.players[player1].score * 0.85
                ):
                    self.p_manager.players[player2].score = math.sqrt(
                        self.p_manager.players[player2].score ** 2
                        + self.p_manager.players[player1].score ** 2
                    )  # adding areas instead of radii
                    self.p_manager.players[player1].score = 0
                    (
                        self.p_manager.players[player1].position.x,
                        self.p_manager.players[player1].position.y,
                    ) = self.p_manager._get_start_location()
                    print(
                        f"[GAME] "
                        + self.p_manager.players[player2].name
                        + " ATE "
                        + self.p_manager.players[player1].name
                    )

    def create_food(self, n):
        """
        Create food cells on the map

        :param food: existing list of food cells
        :param n: the number of food cells to create
        """
        for _ in range(n):
            while True:
                stop = True
                position = random_position(self.cfg.server.w, self.cfg.server.h)
                for player in self.p_manager.players.items():
                    p = self.p_manager.players[player]
                    dis = math.sqrt(
                        (position.x - p.position.x) ** 2
                        + (position.y - p.position.y) ** 2
                    )
                    if dis <= self.cfg.player.player_radius + p["score"]:
                        stop = False
                if stop:
                    break

            self.f_manager.add(position)


class Server:
    def __init__(self, cfg: DictConfig):
        self.cfg = ServerConfig(cfg)

        self.p_manager = PlayerManager(cfg.player)
        self.f_manager = FoodCellManager(cfg.food)
        self.server_logic = ServerLogic(cfg, self.p_manager, self.f_manager)
        self.connections = 0
        self._id = 0
        self.game_time = "Starting Soon"
        self.start = False
        self.start_time = 0

    def bind_server(self):
        try:
            self.cfg.socket.bind((self.cfg.hostname, self.cfg.port))
        except socket.error as e:
            print(str(e))
            print("[SERVER] Server could not start")
            quit()

    def listen_for_connections(self):
        self.cfg.socket.listen()
        print(f"[SERVER] Local ip {self.cfg.hostname}")

    def save_ip(self):
        with open("ip.txt", "w", encoding="utf-8") as file:
            file.write(self.cfg.hostname)

    def start_server(self):
        self.bind_server()
        self.listen_for_connections()
        self.save_ip()

        print("[SERVER] Waiting for connections")
        print("[INFO] Setting up level")
        self.server_logic.create_food(random.randrange(200, 250))

        # Keep looping to accept new connections
        while True:
            host, addr = self.cfg.socket.accept()
            if addr[0] == self.cfg.hostname and not self.start:
                self.start = True
                self.start_time = time.time()
                print("[INFO] Game Started")

            self.connections += 1
            start_new_thread(target=self.threaded_client, args=(host, self._id)).start()
            self._id += 1

        print("[SERVER] Server offline")

    def threaded_client(self, conn, _id):
        """
        Runs in a new thread for each player connected to the server

        :param con: ip address of connection
        :param _id: int
        :return: None
        """
        this_player_id = _id

        # Receive a name from the client
        name = conn.recv(16).decode("utf-8")

        print(f"[INFO] {name}\tconnected")

        # Setup properties for each new player
        self.p_manager.add(name)

        # pickle data and send initial info to clients
        conn.send(str.encode(str(this_player_id)))

        while True:
            if self.start:
                game_time = round(time.time() - self.start_time)
                # if the game time passes the round time the game will stop
                if game_time >= self.cfg.round_time:
                    self.start = False

            try:
                # Receive data from client
                data = conn.recv(self.cfg.buffer_size)

                if not data:
                    break

                data = data.decode("utf-8")

                if data.split(" ")[0] == "move":
                    self.p_manager.handle_move_command(data, this_player_id)

                    self.server_logic.player_food_collision()
                    self.server_logic.player_collisions()

                    # if the amount of food is less than 150 create more
                    if len(self.f_manager.food_cells) <= 250:
                        self.server_logic.create_food(1)
                elif data.split(" ")[0] == "get":
                    send_data = pickle.dumps(
                        (self.f_manager.food_cells, self.p_manager.players, game_time)
                    )
                    # send data back to clients
                    conn.send(send_data)

            except Exception as e:
                print(e)
                break  # if an exception has been reached disconnect client

            time.sleep(0.01)

        # When user disconnects
        print(f"[INFO] {name}\tdisconnected")

        self.connections -= 1
        # remove client information from players list
        self.p_manager.remove(this_player_id)
        conn.close()  # close connection


# Set up a basic logger
logging.basicConfig(level=logging.INFO)


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    server = Server(cfg)
    server.start_server()


if __name__ == "__main__":
    main()
