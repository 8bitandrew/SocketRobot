import socket, struct
from pynput import keyboard

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = msg.encode()
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def on_key_release(key):
    key_char = '%s' % key
    send_key = False
    if key_char == '\'e\'':
        message = 'close'
        send_msg(client, message)
        print('Released Key %s' % key)
        client.close()
        return False
    elif key_char == '\'q\'':
        message = 'exit'
        send_msg(client, message)
        print('Released Key %s' % key)
        client.close()
        return False
    else:
        global forwardvar
        global backwardvar
        global leftvar
        global rightvar
        if key_char == '\'w\'' and forwardvar:
            send_key = True
        elif key_char =='\'a\'' and leftvar:
            send_key = True
        elif key_char =='\'s\'' and backwardvar:
            send_key = True
        elif key_char =='\'d\'' and rightvar:
            send_key = True

        if send_key:
            message = '%s release' % key
            send_msg(client, message)
            print('Released Key %s' % key)

        if key_char == '\'w\'':
            forwardvar = False
        elif key_char =='\'a\'':
            leftvar = False
        elif key_char =='\'s\'':
            backwardvar = False
        elif key_char =='\'d\'':
            rightvar = False
    

def on_key_press(key):
    global forwardvar
    global backwardvar
    global leftvar
    global rightvar

    key_char = '%s' % key
    send_key = False
    if key_char == '\'w\'' and not forwardvar:
        send_key = True
    elif key_char =='\'a\'' and not leftvar:
        send_key = True
    elif key_char =='\'s\'' and not backwardvar:
        send_key = True
    elif key_char =='\'d\'' and not rightvar:
        send_key = True

    if send_key:
        message = '%s press' % key
        send_msg(client, message)
        print('Pressed Key %s' % key)

    if key_char == '\'w\'':
        forwardvar = True
    elif key_char =='\'a\'':
        leftvar = True
    elif key_char =='\'s\'':
        backwardvar = True
    elif key_char =='\'d\'':
        rightvar = True

def client_connect(): 
    #client.settimeout(300) # seconds
    client.connect(("192.168.1.117", 6678)) 
    print("Successful connection to PiRobot socket")

    with keyboard.Listener(on_press = on_key_press, on_release = on_key_release, supress=True) as listener:
        listener.join()

# run code below
# we need to know the state these are in so that we aren't spamming the server with the same key
forwardvar = False
backwardvar = False
leftvar = False
rightvar = False

client = socket.socket() # declare this globablly so our key presses can send messages
client_connect()