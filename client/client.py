import os
import socket

import _pickle as pickle

HEADERSIZE = 10


class Client:
    """
    class to connect, send and recieve information from the server

    need to hardcode the host attirbute to be the server's ip
    """

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[INFO]\tClient created")
        # Read IP from file
        with open("ip.txt", "r") as f:
            self.host = f.read()
        # self.client.settimeout(10.0)
        self.port = 5555
        self.addr = (self.host, self.port)

    def connect(self, name):
        """
        connects to server and returns the id of the client that connected
        :param name: str
        :return: int reprsenting id
        """
        self.sock.connect(self.addr)
        self.sock.send(str.encode(name))
        val = self.sock.recv(1024)
        return int(val.decode())  # can be int because will be an int id

    def disconnect(self):
        """
        disconnects from the server
        :return: None
        """
        self.sock.close()

    def send(self, data, pick=False):
        """
        sends information to the server

        :param data: str
        :param pick: boolean if should pickle or not
        :return: str
        """
        try:
            if pick:
                self.sock.send(pickle.dumps(data))
            else:
                self.sock.send(str.encode(data))

            # Receive data from server
            reply = self.sock.recv(20000)
            reply = pickle.loads(reply)
        except Exception as e:
            # Print all debug information
            print(f"Exception: {e}")
            print(f"data: {data}")

        return reply
