import socket, struct, keyboard

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = msg.encode()
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def on_forward_press(self):
    global forwardvar
    global input_mode
    if not forwardvar and not input_mode:
        message = "forward press"
        send_msg(client, message)
        forwardvar = True
        print("Forward pressed")

def on_backward_press(self):
    global backwardvar
    global input_mode
    if not backwardvar and not input_mode:
        message = "backward press"
        send_msg(client, message)
        backwardvar = True
        print("Backward pressed")

def on_left_press(self):
    global leftvar
    global input_mode
    if not leftvar and not input_mode:
        message = "left press"
        send_msg(client, message)
        leftvar = True
        print("Left pressed")

def on_right_press(self):
    global rightvar
    global input_mode
    if not rightvar and not input_mode:
        message = "right press"
        send_msg(client, message)
        rightvar = True
        print("Right pressed")

def on_forward_release(self):
    global forwardvar
    global input_mode
    if forwardvar and not input_mode:
        message = "forward release"
        send_msg(client, message)
        forwardvar = False
        print("Forward released")

def on_backward_release(self):
    global backwardvar
    global input_mode
    if backwardvar and not input_mode:
        message = "backward release"
        send_msg(client, message)
        backwardvar = False
        print("Backward released")

def on_left_release(self):
    global leftvar
    global input_mode
    if leftvar and not input_mode:
        message = "left release"
        send_msg(client, message)
        leftvar = False
        print("Left released")

def on_right_release(self):
    global rightvar
    global input_mode
    if rightvar and not input_mode:
        message = "right release"
        send_msg(client, message)
        rightvar = False
        print("Right released")

def on_speed_1_release(self):
    global speed
    global input_mode
    if speed != 25 and not input_mode:
        message = "speed 25"
        send_msg(client, message)
        speed = 25
        print("Speed set to 25%")

def on_speed_2_release(self):
    global speed
    global input_mode
    if speed != 50 and not input_mode:
        message = "speed 50"
        send_msg(client, message)
        speed = 50
        print("Speed set to 50%")

def on_speed_3_release(self):
    global speed
    global input_mode
    if speed != 75 and not input_mode:
        message = "speed 75"
        send_msg(client, message)
        speed = 75
        print("Speed set to 75%")

def on_speed_4_release(self):
    global speed
    global input_mode
    if speed != 100 and not input_mode:
        message = "speed 100"
        send_msg(client, message)
        speed = 100
        print("Speed set to 100%")

def stop_all_motors(self):
    global forwardvar
    global backwardvar
    global leftvar
    global rightvar

    if forwardvar:
        on_forward_release()
    if backwardvar:
        on_backward_release()
    if leftvar:
        on_left_release()
    if rightvar:
        on_right_release()

def on_text_to_speech(self):
    global input_mode
    stop_all_motors()
    input_mode = True
    message = "speech:"
    message += input("Enter text for robot to say: ")
    send_msg(client, message)
    input_mode = False
    print("Sent text to robot")

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

def quit():
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

    keyboard.on_release_key('1', on_speed_1_release, suppress=True)
    keyboard.on_release_key('2', on_speed_2_release, suppress=True)
    keyboard.on_release_key('3', on_speed_3_release, suppress=True)
    keyboard.on_release_key('4', on_speed_4_release, suppress=True)

    keyboard.on_press_key('t', on_text_to_speech, supress=True)

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
speed = 100
input_mode = False
quit_client = False

client = socket.socket() # declare this globablly so our key presses can send messages
client_connect()