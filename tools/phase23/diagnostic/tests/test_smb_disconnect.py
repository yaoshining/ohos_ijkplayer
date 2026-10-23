import importlib.util
from pathlib import Path
import socket
import unittest
p=Path(__file__).resolve().parents[1]/"smb_disconnect.py"
s=importlib.util.spec_from_file_location("disconnect",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Disconnect(unittest.TestCase):
 def test_only_dedicated_file_is_disconnected_once(self):
  d=m.DisconnectOnce()
  a,b=socket.socketpair()
  try:
   self.assertFalse(d.before_read("/fixtures/seek.bin",a))
   a.sendall(b"x");self.assertEqual(b.recv(1),b"x")
   self.assertTrue(d.before_read("/fixtures/__phase23_disconnect.bin",a))
   self.assertEqual(b.recv(1),b"")
  finally:a.close();b.close()
  a,b=socket.socketpair()
  try:
   self.assertFalse(d.before_read("/fixtures/__phase23_disconnect.bin",a))
   a.sendall(b"y");self.assertEqual(b.recv(1),b"y")
  finally:a.close();b.close()
if __name__=="__main__":unittest.main()
