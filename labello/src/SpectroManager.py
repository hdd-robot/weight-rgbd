#!/usr/bin/python3
import base64
import socket
import json
from Params import *

class SpectroManager:
    def __init__(self):
        self.prms = Params()
        self.ip =  self.prms.get_spectro_ip()
        self.port = self.prms.get_spectro_port()
        # print(self.ip , ":", self.port)
        self.addr = (self.ip, self.port)
        self.size = 100000
        self.data_array = []

    def get_data(self):
        try:
            """ Staring a TCP socket. """
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            """ Connecting to the server. """
            client.connect(self.addr)

            """ Sending the filename to the server. """
            client.send("GET_DATA".encode("utf-8"))
        except:
            return False

        try :
            msg = client.recv(self.size).decode("utf-8")
            recv_data = msg
            while (len(msg)):
                msg = client.recv(self.size).decode("utf-8")
                recv_data = recv_data + msg

            print(f"[SERVER]: {str(len(recv_data))} chars")
            """ Sending the file data to the server. """

            json_obj = json.loads(recv_data)
            image_specter = json.dumps(json_obj['image_specter'])

            specter_file_name = "specter.png"
            with open(specter_file_name, "wb") as fh:
                img = base64.b64decode(image_specter)
                fh.write(img)

            image_graphe = json.dumps(json_obj['image_graphe'])

            graph_file_name = "graph.png"
            with open(graph_file_name, "wb") as fh:
                img = base64.b64decode(image_graphe)
                fh.write(img)


            self.data_array = json.dumps(json_obj['data_array'])
        except Exception as e:
            print (e)
            return False

        client.close()
        return [self.data_array, specter_file_name, graph_file_name]

    def check_spectro_connected(self):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            """ Connecting to the server. """
            client.connect(self.addr)
        except ConnectionRefusedError:
            print("Can't establish spectroscope connexion : IP " + self.ip + ' port ' + str(self.port))
            return False
        except Exception as e:
            print(e)
            return False

        return True

        return False
