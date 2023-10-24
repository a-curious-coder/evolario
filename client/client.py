import os
import socket
import traceback

import _pickle as pickle


class Client:
    """
    class to connect, send and recieve information from the server

    need to hardcode the host attirbute to be the server's ip
    """

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[INFO]\tClient created")
        # Read IP from file
        with open("ip.txt") as ip_file:
            self.host = ip_file.read()
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
        val = self.sock.recv(200000)
        return int(val.decode())  # can be int because will be an int id

    def disconnect(self):
        """
        disconnects from the server
        :return: None
        """
        self.sock.close()

    def send(self, data):
        """
        sends information to the server

        :param data: str
        :param pick: boolean if should pickle or not
        :return: str
        """
        # Send request to server
        self.sock.send(str.encode(data))

        full_response = self.sock.recv(200000)
        print(f"[INFO]\tFull response size: {len(full_response)}")
        reply = pickle.loads(full_response)

        return reply

    def send2(self, data):
        """
        sends information to the server

        :param data: str
        :param pick: boolean if should pickle or not
        :return: str
        """
        # Send request to server
        self.sock.send(str.encode(data))
        full_response = b""
        while True:
            # Receive data from server
            response = self.sock.recv(200000)
            # Append the response to the full_response
            full_response += response
            # Print full response size
            print(f"[INFO]\tFull response size: {len(full_response)}")
            # If response is empty, break the loop
            if len(response) == 0:
                break

        # Decode data from server
        reply = pickle.loads(full_response)

        return reply
