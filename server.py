"""
main server script for running agar.io server

can handle multiple/infinite connections on the same
local network
"""
import logging
import math
import random
import socket
import time
from _thread import *

import _pickle as pickle

from game import Food, Player, Position

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
# Define constants
BUFFER_SIZE = 32

# Setup sockets
S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Set constants
PORT = 5555

PLAYER_RADIUS = 20

ROUND_TIME = 60 * 1000

MASS_LOSS_TIME = 7

W, H = 1920, 1080

HOST_NAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(HOST_NAME)

# try to connect to server
try:
    S.bind((SERVER_IP, PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Server could not start")
    quit()

S.listen()  # listen for connections

print(f"[SERVER] Local ip {SERVER_IP}")
# Save IP to file
with open("ip.txt", "w") as f:
    f.write(SERVER_IP)


# dynamic variables
players = {}
food = []
connections = 0
_id = 0
colors = [
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
start = False
start_time = 0
game_time = "Starting Soon"


def release_mass(players):
    """
    releases the mass of players

    :param players: dict
    :return: None
    """
    for player in players:
        p = players[player]
        if p["score"] > 8:
            p["score"] = math.floor(p["score"] * 0.95)


def check_collision_food(players, food):
    """
    checks if any of the player have collided with any of the food

    :param players: a dictonary of players
    :param food: a list of food
    :return: None
    """
    for player in players:
        p = players[player]
        playerX = p["x"]
        playerY = p["y"]
        for cell in food:
            foodX = cell[0]
            foodY = cell[1]

            dis = math.sqrt((playerX - foodX) ** 2 + (playerY - foodY) ** 2)
            if dis <= PLAYER_RADIUS + p["score"]:
                p["score"] = p["score"] + 1
                food.remove(cell)


def check_collision_player(players):
    """
    checks for player collision and handles that collision

    :param players: dict
    :return: None
    """
    sort_players = sorted(players, key=lambda x: players[x]["score"])
    for x, player1 in enumerate(sort_players):
        for player2 in sort_players[x + 1 :]:
            p1x = players[player1]["x"]
            p1y = players[player1]["y"]

            p2x = players[player2]["x"]
            p2y = players[player2]["y"]

            dis = math.sqrt((p1x - p2x) ** 2 + (p1y - p2y) ** 2)
            if dis < players[player2]["score"] - players[player1]["score"] * 0.85:
                players[player2]["score"] = math.sqrt(
                    players[player2]["score"] ** 2 + players[player1]["score"] ** 2
                )  # adding areas instead of radii
                players[player1]["score"] = 0
                players[player1]["x"], players[player1]["y"] = get_start_location(
                    players
                )
                print(
                    f"[GAME] "
                    + players[player2]["name"]
                    + " ATE "
                    + players[player1]["name"]
                )


def create_food(food_cells, n):
    """
    Create food cells on the map

    :param food: existing list of food cells
    :param n: the number of food cells to create
    """
    for _ in range(n):
        while True:
            stop = True
            x = random.randrange(0, W)
            y = random.randrange(0, H)
            for player in players:
                p = players[player]
                dis = math.sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2)
                if dis <= PLAYER_RADIUS + p["score"]:
                    stop = False
            if stop:
                break

        food_cells.append((x, y, random.choice(colors)))


def get_start_location(players):
    """
    picks a start location for a player based on other player
    locations. It will ensure it does not spawn inside another player

    :param players: dict
    :return: tuple (x,y)
    """
    while True:
        stop = True
        x = random.randrange(0, W)
        y = random.randrange(0, H)
        for player in players:
            p = players[player]
            dis = math.sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2)
            if dis <= PLAYER_RADIUS + p["score"]:
                stop = False
                break
        if stop:
            break
    return Position(x, y)


def handle_move_command(data, current_id):
    split_data = data.split(" ")
    x = int(split_data[1])
    y = int(split_data[2])
    players[current_id]["x"] = x
    players[current_id]["y"] = y


def threaded_client(conn, _id):
    """
    Runs in a new thread for each player connected to the server

    :param con: ip address of connection
    :param _id: int
    :return: None
    """
    global connections, players, food, game_time, start

    current_id = _id

    # Receive a name from the client
    data = conn.recv(16)
    name = data.decode("utf-8")

    print(f"[INFO] {name}\tconnected")

    # Setup properties for each new player
    position = get_start_location(players)
    players[current_id] = Player(name, position, 0)

    # pickle data and send initial info to clients
    conn.send(str.encode(str(current_id)))

    start_time = time.time()
    while True:
        if start:
            game_time = round(time.time() - start_time)
            # if the game time passes the round time the game will stop
            if game_time >= ROUND_TIME:
                start = False

        try:
            # Receive data from client
            data = conn.recv(BUFFER_SIZE)

            if not data:
                break

            data = data.decode("utf-8")

            if data.split(" ")[0] == "move":
                handle_move_command(data, current_id)

                check_collision_food(players, food)
                check_collision_player(players)

                # if the amount of food is less than 150 create more
                if len(food) <= 250:
                    create_food(food, 1)
            elif data.split(" ")[0] == "get":
                send_data = pickle.dumps((food, players, game_time))
                # send data back to clients
                conn.send(send_data)

        except Exception as e:
            print(e)
            break  # if an exception has been reached disconnect client

        time.sleep(0.01)

    # When user disconnects
    print(f"[INFO] {name}\tdisconnected")

    connections -= 1
    del players[current_id]  # remove client information from players list
    conn.close()  # close connection


def main():
    print("[SERVER] Waiting for connections")
    print("[INFO] Setting up level")
    global start, start_time, connections, _id
    # Initialise the level with food
    create_food(food, random.randrange(200, 250))
    start = False
    try:
        # Keep looping to accept new connections
        while True:
            host, addr = S.accept()
            # print("[INFO] Connected to:", addr)

            # start game when a client on the server computer connects
            if addr[0] == SERVER_IP and not (start):
                start = True
                start_time = time.time()
                print("[INFO] Game Started")

            # increment connections start new thread then increment ids
            connections += 1
            start_new_thread(threaded_client, (host, _id))
            _id += 1

        # when program ends
        print("[SERVER] Server offline")
    except KeyboardInterrupt as k:
        print("Keyboard Interrupt")


if __name__ == "__main__":
    main()
