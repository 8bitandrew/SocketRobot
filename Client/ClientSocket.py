import socket
import struct
from pynput import keyboard

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = msg.encode()
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def on_key_release(key):
    exit_key = '%s' % key
    if exit_key == '\'e\'':
        message = 'close'
        send_msg(client, message)
        print('Released Key %s' % key)
        client.close()
        return False
    elif exit_key == '\'q\'':
        message = 'exit'
        send_msg(client, message)
        print('Released Key %s' % key)
        client.close()
        return False
    else:
        message = '%s release' % key
        send_msg(client, message)
        print('Released Key %s' % key)

def on_key_press(key):
    message = '%s press' % key
    send_msg(client, message)
    print('Pressed Key %s' % key)

def client_connect(): 
    client.settimeout(2) # seconds
    client.connect(("192.168.1.117", 6678)) 
    print("Successful connection to PiRobot socket")

    with keyboard.Listener(on_press = on_key_press, on_release = on_key_release) as listener:
        listener.join()

# run code below
client = socket.socket() # declare this globablly so our key presses can send messages
client_connect()