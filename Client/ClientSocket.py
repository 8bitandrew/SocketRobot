import socket, struct, keyboard

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = msg.encode()
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def on_forward_press(self):
    global forwardvar
    if not forwardvar:
        message = "forward press"
        send_msg(client, message)
        forwardvar = True
        print("Forward pressed")

def on_backward_press(self):
    global backwardvar
    if not backwardvar:
        message = "backward press"
        send_msg(client, message)
        backwardvar = True
        print("Backward pressed")

def on_left_press(self):
    global leftvar
    if not leftvar:
        message = "left press"
        send_msg(client, message)
        leftvar = True
        print("Left pressed")

def on_right_press(self):
    global rightvar
    if not rightvar:
        message = "right press"
        send_msg(client, message)
        rightvar = True
        print("Right pressed")

def on_forward_release(self):
    global forwardvar
    if forwardvar:
        message = "forward release"
        send_msg(client, message)
        forwardvar = False
        print("Forward released")

def on_backward_release(self):
    global backwardvar
    if backwardvar:
        message = "backward release"
        send_msg(client, message)
        backwardvar = False
        print("Backward released")

def on_left_release(self):
    global leftvar
    if leftvar:
        message = "left release"
        send_msg(client, message)
        leftvar = False
        print("Left released")

def on_right_release(self):
    global rightvar
    if rightvar:
        message = "right release"
        send_msg(client, message)
        rightvar = False
        print("Right released")

def on_close_socket_release(self):
    message = "close"
    send_msg(client, message)
    client.close()
    print("Close socket")
    quit()

def on_exit_release(self):
    message = "exit"
    send_msg(client, message)
    client.close()
    print("Exit program")
    quit()

def quit(self):
    global quit_client
    quit_client = True

def client_connect(): 
    #client.settimeout(300) # seconds
    client.connect(("192.168.1.117", 6678)) 
    print("Successful connection to PiRobot socket")

    keyboard.on_press_key('w', on_forward_press, suppress=True)
    keyboard.on_press_key('a', on_left_press, suppress=True)
    keyboard.on_press_key('s', on_backward_press, suppress=True)
    keyboard.on_press_key('d', on_right_press, suppress=True)

    keyboard.on_release_key('w', on_forward_release, suppress=True)
    keyboard.on_release_key('a', on_left_release, suppress=True)
    keyboard.on_release_key('s', on_backward_release, suppress=True)
    keyboard.on_release_key('d', on_right_release, suppress=True)

    keyboard.on_release_key('e', on_close_socket_release, suppress=True)
    keyboard.on_release_key('q', on_exit_release, suppress=True)

    while not quit_client:
        pass

# run code below
# we need to know the state these are in so that we aren't spamming the server with the same key
forwardvar = False
backwardvar = False
leftvar = False
rightvar = False
quit_client = False

client = socket.socket() # declare this globablly so our key presses can send messages
client_connect()