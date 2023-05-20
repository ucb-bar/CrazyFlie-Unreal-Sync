import time
import socket
import struct
import threading

class UnrealBridge:
    def __init__(self, port=8080):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_stopped = threading.Event()

        self.sock.bind(("", port))
        self.sock.listen(1)
        self.sock.settimeout(1)

        self.data = {}
    
        self.setData("/x", 0)
        self.setData("/y", 0)
        self.setData("/z", 0)
        self.setData("/pitch", 0)
        self.setData("/roll", 0)
        self.setData("/yaw", 0)
        
    def getData(self, key):
        return self.data.get(key)

    def setData(self, key, value):
        self.data[key] = value

    def run(self):
        while not self.is_stopped.is_set():
            print("waiting connection")
            conn = None
            while not conn and not self.is_stopped.is_set():
                try:
                    conn, addr = self.sock.accept()
                except TimeoutError:
                    continue
                except OSError:
                    return

            print("connected by", addr)

            # disregard garbage
            conn.recv(12)

            try:
                while not self.is_stopped.is_set():
                    x = self.getData("/x")
                    y = self.getData("/y")
                    z = self.getData("/z")
                    pitch = self.getData("/pitch")
                    roll = self.getData("/roll")
                    yaw = self.getData("/yaw")
                    
                    size = 4 * 6
                    buffer = struct.pack(">BBffffff", 1, size, x, y, z, pitch, roll, yaw)
                    #buffer += content.encode()
                    try:
                        conn.sendall(buffer)
                    except (ConnectionResetError, ConnectionAbortedError):
                        print("connection closed")
                        break

                    try:
                        buffer = conn.recv(2)
                        if not buffer:
                            continue
                        message_type, length = struct.unpack(">BB", buffer)
                        if message_type != 1:
                            print("error in frame")
                            continue
                        buffer = conn.recv(length)
                        print(length, struct.unpack(">fff", buffer))
                    except (ConnectionResetError, ConnectionAbortedError):
                        print("connection closed")
                        break

            except KeyboardInterrupt:
                print("interrupted")

    def start(self):
        self.is_stopped.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.is_stopped.set()
        self.sock.close()
