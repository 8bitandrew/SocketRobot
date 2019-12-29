import socket
from pynput import keyboard

server = socket.socket() 
server.connect(("10.0.1.15", 6678)) 
print("Successful connection to PiRobot socket")

def on_key_release(key):
    message = '%s release'
    message = message.encode()
    server.send(message)
    print('Released Key %s' % key)
    #msg = server.recv(1024)
    #print("Message from server : " + msg.decode())

def on_key_press(key):
    message = '%s press'
    message = message.encode()
    server.send(message)
    print('Pressed Key %s' % key)
    #msg = server.recv(1024)
    #print("Message from server : " + msg.decode())

with keyboard.Listener(
    on_press = on_key_press,
    on_release = on_key_release) as listener:
    listener.join()
