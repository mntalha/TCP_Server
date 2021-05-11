#!/usr/bin/env python3

import _thread
import socket
import select
import queue
import threading

class TcpServer:
    def __init__(self, local_port, timeout=None):
        print("\nTCP Server Running\n")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', local_port))
        self.server_socket.listen(10)

        self.RECV_BUFFER = 4096  # Advisable to keep it as an exponent of 2
        self.CONNECTION_LIST = []  # list of socket clients
        self.CONNECTION_LIST.append(self.server_socket)  # Add server socket to the list of readable connections
        print("Server started on port " + str(local_port))

        self.socket = None

        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(10)

        _thread.start_new_thread(self.socket_server_reader, ())

    def socket_server_reader(self):
        # receiving data from tcp client
        while True:
            # Get the list sockets which are ready to be read through select
            read_sockets, write_sockets, error_sockets = select.select(self.CONNECTION_LIST, [], [])
            for sock in read_sockets:
                # New connection
                if sock == self.server_socket:
                    # Handle the case in which there is a new connection received through server_socket
                    self.socket, addr = self.server_socket.accept()
                    self.socket.settimeout(1)
                    self.CONNECTION_LIST.append(self.socket)
                    print("Client (%s, %s) connected" % addr)
                else:
                    # Data received from client, process it
                    try:
                        # In Windows, sometimes when a TCP program closes abruptly,
                        # a "Connection reset by peer" exception will be thrown
                        data = sock.recv(self.RECV_BUFFER)
                        if data:
                            self.queueLock.acquire()
                            self.workQueue.put(data)
                            self.queueLock.release()
                    except:
                        print("Client (%s, %s) is offline" % addr)
                        sock.close()
                        # client disconnected, so remove from socket list
                        self.CONNECTION_LIST.remove(sock)
                        continue

    def read_queue(self):
        self.queueLock.acquire()
        data = None
        if not self.workQueue.empty():
            data = self.workQueue.get().decode("utf-8")
        self.queueLock.release()
        return data

    def socket_send_message(self, message):
        # transmitting data to tcp client
        try:
            self.socket.sendall(bytes(message, 'utf-8'))
        except socket.error as msg:  # probably got disconnected
            print(msg)


# ======================================================================================================================
def self_tcp_server_run(port_number):
    r = TcpServer(port_number, 1)

    while True:
        data = r.read_queue()
        if data:
            print(data)
            r.socket_send_message("Hello Response")




# ======================================================================================================================
if __name__ == '__main__':
    self_tcp_server_run(4200)
    print("\n--- exit ---")


# ======================================================================================================================

