"""
Author: Alex Perrakis
Description: A simple Command & Control Server.
"""

from PyQt5.QtWidgets import *
from PyQt5 import uic
import asyncio
import sys
import socket
import threading
from PyQt5.QtCore import Qt 
from PyQt5.QtGui import QColor
import time

class MyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("server.ui", self)

        # Connect button click to a function
        self.startServerBtn.clicked.connect(self.on_start_server_clicked)
        self.executeBtn.clicked.connect(self.on_batch_execute_clicked)

        # Store connected clients
        self.connected_clients = []

        # Initialize asyncio variables
        self.asyncio_loop = None
        self.server = None

        # Set label styles
        self.serverStatusLabel.setStyleSheet("color: red")

        # Set column widths
        self.tableWidget.setColumnWidth(0, 200)
        self.tableWidget.setColumnWidth(1, 350)
        self.tableWidget.setColumnWidth(2, 169)

        # Start the thread to check client connections
        # self.check_connections_thread = threading.Thread(target=self.check_client_connections)
        # self.check_connections_thread.daemon = True  # Set the thread as daemon
        # self.check_connections_thread.start()

        self.show()

    # Function to check client connections
    def check_client_connections(self):
        while True:
            disconnected_clients = []
            for reader, writer in self.connected_clients:
                try:
                    # Attempt a non-blocking read operation to check client status
                    data = reader.read_nowait()  # Change this line to match your read method

                    # If the read operation succeeds, the client is still connected
                except Exception as e:
                    # If an exception occurs (indicating a disconnection), handle it
                    client_ip = "Unknown"  # As client IP isn't stored, use a placeholder
                    print(f"Client disconnected")
                    disconnected_clients.append((reader, writer))

            for disconnected_client in disconnected_clients:
                self.connected_clients.remove(disconnected_client)
                client_info = ("Unknown", "", "Offline")  # Assuming IP is unknown
                self.update_table_widget(client_info)

            time.sleep(5)  # Check every 5 seconds

    # Handle batch execution button click
    def on_batch_execute_clicked(self):
        message_to_send = self.textEdit.toPlainText().encode('utf-8')
        if self.asyncio_loop is not None:
            asyncio.run_coroutine_threadsafe(self.send_messages(message_to_send), self.asyncio_loop)

    # Send messages to connected clients
    async def send_messages(self, message):
        for reader, writer in self.connected_clients:
            writer.write(message)
            writer.write(b'\n')
            await writer.drain()

    # Stop the server
    def stop_server(self):
        if self.server:
            self.server.close()
            self.asyncio_loop.run_until_complete(self.server.wait_closed())
            self.asyncio_loop.stop()

    # Handle start server button click
    def on_start_server_clicked(self):
        if self.startServerBtn.text() == "Start Server":
            self.asyncio_thread = threading.Thread(target=self.start_asyncio_server)
            self.asyncio_thread.start()
            self.serverStatusLabel.setText("Server online at port 8888")
            self.serverStatusLabel.setStyleSheet("color: green")
            self.startServerBtn.setText("Stop Server")
        else:            
            self.stop_server()
            self.serverStatusLabel.setText("Server offline")
            self.serverStatusLabel.setStyleSheet("color: red")
            self.startServerBtn.setText("Start Server")

    # Handle client connections
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        client_ip = addr[0]
        os_type = await reader.read(1024)
        os_type = os_type.decode().strip()
        client_info = (client_ip, os_type, "Connected")

        self.connected_clients.append((reader, writer))
        self.update_table_widget(client_info)

    # Start the asyncio server
    def start_asyncio_server(self):
        self.asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.asyncio_loop)

        async def start_server():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('0.0.0.0', 8888))
            server_sock.listen()

            server = await asyncio.start_server(self.handle_client, sock=server_sock)

            async with server:
                print("Server started on port 8888. Waiting for connections...")
                await server.serve_forever()

        self.asyncio_loop.run_until_complete(start_server())

    # Update table widget with client info
    def update_table_widget(self, client_info):
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)
        
        ip_item, os_item, status_item = map(QTableWidgetItem, client_info)

        for item in (ip_item, os_item, status_item):
            item.setTextAlignment(Qt.AlignCenter)

        if client_info[2] == "Connected":
            status_item.setForeground(QColor('green'))
        else:
            status_item.setForeground(QColor('red'))

        self.tableWidget.setItem(row_position, 0, ip_item)
        self.tableWidget.setItem(row_position, 1, os_item)
        self.tableWidget.setItem(row_position, 2, status_item)

    # Terminate asyncio loop when window is closed
    def closeEvent(self, event):
        if self.asyncio_loop and not self.asyncio_loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.asyncio_loop.shutdown_asyncgens(), self.asyncio_loop)
            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.close)
            self.asyncio_thread.join()
        event.accept()

def main():
    app = QApplication([])
    window = MyGUI()
    app.exec_()

if __name__ == '__main__':
    main()
