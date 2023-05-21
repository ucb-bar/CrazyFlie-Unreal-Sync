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
        
    def getData(self, key, default=None):
        try:
            val = self.data[key]
        except KeyError:
            return default
        return val

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
                    x = self.getData("/x", 0)
                    y = self.getData("/y", 0)
                    z = self.getData("/z", 0)
                    pitch = self.getData("/pitch", 0)
                    roll = self.getData("/roll", 0)
                    yaw = self.getData("/yaw", 0)
                    
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
                        
                        cmd_x, cmd_y, cmd_z, cmd_yaw, is_stopped = struct.unpack(">ffffB", buffer)

                        self.setData("/cmd_x", cmd_x)
                        self.setData("/cmd_y", cmd_y)
                        self.setData("/cmd_z", cmd_z)
                        self.setData("/cmd_yaw", cmd_yaw)
                        self.setData("/cmd_is_stopped", is_stopped)

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
