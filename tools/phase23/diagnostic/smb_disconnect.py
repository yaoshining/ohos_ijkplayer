"""One controlled socket shutdown for the dedicated recovery fixture."""
import socket
import threading
from pathlib import Path

class DisconnectOnce:
    def __init__(self):
        self.lock=threading.Lock()
        self.done=False
    def before_read(self, name, sock):
        if Path(name).name != "__phase23_disconnect.bin":
            return False
        with self.lock:
            if self.done:
                return False
            sock.shutdown(socket.SHUT_RDWR)
            self.done=True
            return True
