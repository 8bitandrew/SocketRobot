import socket
import threading
import struct
from enum import Enum
import RPi.GPIO as gpio

class robotThread (threading.Thread):
    class State(Enum):
            NONE = 0
            FORWARD = 1
            BACKWARD = 2
            LEFT = 3
            RIGHT = 4

    current_state = State.NONE.value
    
    controlled_by_username = "" # TODO eventually multiple clients will be connecting to this socket.
    # We will need to know who currently has control over the robot to avoid multiple inputs at once

    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def initialize():
        gpio.setmode(gpio.BOARD)
        gpio.setup(33, gpio.OUT)
        gpio.setup(36, gpio.OUT)
        gpio.setup(35, gpio.OUT)
        gpio.setup(37, gpio.OUT)
        gpio.setup(38, gpio.OUT)
        gpio.setup(40, gpio.OUT)
        gpio.output(33, gpio.HIGH)
        gpio.output(36, gpio.HIGH)

    def clear():
        gpio.output(35, gpio.LOW)
        gpio.output(37, gpio.LOW)
        gpio.output(38, gpio.LOW)
        gpio.output(40, gpio.LOW)
        global forwardvar
        global backwardvar
        global leftvar
        global rightvar
        forwardvar = False
        backwardvar = False
        leftvar = False
        rightvar = False

    def cleanup(self):
        self.clear()
        gpio.output(33, gpio.LOW)
        gpio.output(36, gpio.LOW)

    def forward(self):
        self.clear()
        gpio.output(35, gpio.HIGH)
        gpio.output(37, gpio.LOW)
        gpio.output(38, gpio.HIGH)
        gpio.output(40, gpio.LOW)

    def backward(self):
        self.clear()
        gpio.output(35, gpio.LOW)
        gpio.output(37, gpio.HIGH)
        gpio.output(38, gpio.LOW)
        gpio.output(40, gpio.HIGH)

    def swivel_left(self):
        self.clear()
        gpio.output(35, gpio.HIGH)
        gpio.output(37, gpio.LOW)
        gpio.output(38, gpio.LOW)
        gpio.output(40, gpio.HIGH)

    def swivel_right(self):
        self.clear()
        gpio.output(35, gpio.LOW)
        gpio.output(37, gpio.HIGH)
        gpio.output(38, gpio.HIGH)
        gpio.output(40, gpio.LOW)
    
    def interpret_state(self):
        global forwardvar
        global backwardvar
        global leftvar
        global rightvar

        x_state = (leftvar and not rightvar) or (rightvar and not leftvar)
        y_state = (forwardvar and not backwardvar) or (backwardvar and not forwardvar)
        state_to_set = self.State.NONE.value

        if x_state and y_state:
            if self.current_state == self.State.FORWARD.value:
                state_to_set = self.State.BACKWARD.value
            else:
                state_to_set = self.State.FORWARD.value
        elif x_state:
            if leftvar:
                state_to_set = self.State.LEFT.value
            else:
                state_to_set = self.State.RIGHT.value
        elif y_state:
            if forwardvar:
                state_to_set = self.State.FORWARD.value
            else:
                state_to_set = self.State.BACKWARD.value
            
        return state_to_set
    
    def set_motors(self, new_state):
        if new_state == self.State.NONE.value:
            self.clear()
        elif new_state == self.State.FORWARD.value:
            self.forward()
        elif new_state == self.State.BACKWARD.value:
            self.backward()
        elif new_state == self.State.LEFT.value:
            self.swivel_left()
        elif new_state == self.State.RIGHT.value:
            self.swivel_right()
    
    def set_state(self, new_state):
        if new_state != self.current_state:
            self.set_motors(new_state)
            self.current_state = new_state

    def run(self):
        global close_socket
        global exit_program

        gpio.setwarnings(False)
        self.initialize()
        while True:
            if exit_program:
                self.cleanup()
                print("Stopping robot thread...")
                break
            elif close_socket:
                self.clear()
                
            new_state = self.interpret_state()
            self.set_state(new_state)

class socketThread (threading.Thread):
    def __init__(self, ip_address, port, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.ip_address = ip_address
        self.port = port

    def recvall(sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def recv_msg(self, sock):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(sock, msglen)

    def run(self):
        global forwardvar
        global backwardvar
        global leftvar
        global rightvar
        global close_socket
        global exit_program

        socket.setdefaulttimeout(300) # seconds
        server = socket.socket()

        server.bind((self.ip_address, self.port))

        while not exit_program:
            try:
                server.listen(4)
                client_socket, client_address = server.accept()
                print(client_address, "has connected")

                while True:
                    received_data = client_socket.recv(1024)
                    #received_data = self.recv_msg(client_socket)
                    decoded_data = received_data.decode()

                    if decoded_data == 'close':
                        client_socket.close()
                        close_socket = True
                        print(decoded_data)
                        break
                    elif decoded_data == 'exit':
                        client_socket.close()
                        exit_program = True
                        print(decoded_data)
                        break
                    elif decoded_data == '\'w\' press':
                        forwardvar = 1
                        print(decoded_data)
                    elif decoded_data == '\'a\' press':
                        leftvar = 1
                        print(decoded_data)
                    elif decoded_data == '\'s\' press':
                        backwardvar = 1
                        print(decoded_data)
                    elif decoded_data == '\'d\' press':
                        rightvar = 1
                        print(decoded_data)
                    elif decoded_data == '\'w\' release':
                        forwardvar = 0
                        print(decoded_data)
                    elif decoded_data == '\'a\' release':
                        leftvar = 0
                        print(decoded_data)
                    elif decoded_data == '\'s\' release':
                        backwardvar = 0
                        print(decoded_data)
                    elif decoded_data == '\'d\' release':
                        rightvar = 0
                        print(decoded_data)
            except socket.timeout:
                    print("Client timed out...")
                    close_socket = True
                    break
            except Exception as e:
                if exit_program:
                    print(type(e), e)
                    print("Exiting server program...")
                    break
                else:
                    print(type(e), e)
                    pass

def start_server():
    # set local ip and desired port here
    ip_address = "192.168.1.117"
    port = 6678

    threads = []
    RobotThread = robotThread(1, "RobotThread", 1)
    SocketThread = socketThread(ip_address, port, 2, "SocketThread", 2)

    RobotThread.start()
    SocketThread.start()

    threads.append(RobotThread)
    threads.append(SocketThread)
    for t in threads:
        t.join()
    print("Program exited cleanly.")

# run code below
# declare these globally variables so each thread can mutate
forwardvar = False
backwardvar = False
leftvar = False
rightvar = False
close_socket = False
exit_program = False

start_server()