import socket
import threading
import struct
import debugpy
import RPi.GPIO as gpio
from enum import Enum
from multiprocessing import Thread, Lock

class robotThread (threading.Thread):
    class State(Enum):
            NONE = 0
            FORWARD = 1
            BACKWARD = 2
            LEFT = 3
            RIGHT = 4

    current_state = State.NONE.value
    secondary_state_exists = False # used to indicate a second state if two states exist at once
    
    controlled_by_id = 0 # TODO eventually multiple clients will be connecting to this socket.
    # We will need to know who currently has control over the robot to avoid multiple inputs at once

    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def initialize(self):
        gpio.setmode(gpio.BOARD)
        gpio.setup(33, gpio.OUT)
        gpio.setup(36, gpio.OUT)
        gpio.setup(35, gpio.OUT)
        gpio.setup(37, gpio.OUT)
        gpio.setup(38, gpio.OUT)
        gpio.setup(40, gpio.OUT)
        gpio.output(33, gpio.HIGH)
        gpio.output(36, gpio.HIGH)

    def clear(self):
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
        secondary_state_to_set = False

        if x_state and y_state:
            if secondary_state_exists:
                state_to_set = current_state
                secondary_state_to_set = secondary_state_exists
            else:
                secondary_state_to_set = True
                if forwardvar and self.State.FORWARD.value != current_state:
                    state_to_set = self.State.FORWARD.value
                elif backwardvar and self.State.BACKWARD.value != current_state:
                    state_to_set = self.State.BACKWARD.value
                elif leftvar and self.State.LEFT.value != current_state:
                    state_to_set = self.State.LEFT.value
                elif rightvar and self.State.RIGHT.value != current_state:
                    state_to_set = self.State.RIGHT.value
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

        secondary_state = secondary_state_to_set
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
            self.secondary_state = current_state
            self.current_state = new_state

    def run(self):
        global close_socket
        global exit_program
        global motor_state_mutex

        # for remote debugging
        #debugpy.breakpoint()

        gpio.setwarnings(False)
        self.initialize()
        while True:
            if exit_program:
                self.cleanup()
                print("Stopping robot thread...")
                break
            elif close_socket:
                self.clear()
            
            motor_state_mutex.acquire()
            try:
                new_state = self.interpret_state()
                self.set_state(new_state)
            finally:
                motor_state_mutex.release()

class socketThread (threading.Thread):
    def __init__(self, ip_address, port, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.ip_address = ip_address
        self.port = port

    def recvall(self, sock, n):
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
        global motor_state_mutex

        socket.setdefaulttimeout(300) # seconds
        server = socket.socket()
        server.bind((self.ip_address, self.port))

        # for remote debugging
        #debugpy.breakpoint()

        while not exit_program:
            try:
                server.listen(4)
                client_socket, client_address = server.accept()
                print(client_address, "has connected")

                while True:
                    received_data = self.recv_msg(client_socket)
                    decoded_data = received_data.decode()

                    if decoded_data == 'close':
                        client_socket.close()
                        motor_state_mutex.acquire()
                        try:
                            close_socket = True
                        finally:
                            motor_state_mutex.release()
                        print(client_address, "disconnected")
                        break
                    elif decoded_data == 'exit':
                        client_socket.close()
                        motor_state_mutex.acquire()
                        try:
                            exit_program = True
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                        break
                    elif decoded_data == '\'w\' press':
                        motor_state_mutex.acquire()
                        try:
                            forwardvar = True
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'a\' press':
                        motor_state_mutex.acquire()
                        try:
                            leftvar = True
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'s\' press':
                        motor_state_mutex.acquire()
                        try:
                            backwardvar = True
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'d\' press':
                        motor_state_mutex.acquire()
                        try:
                            rightvar = True
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'w\' release':
                        motor_state_mutex.acquire()
                        try:
                            forwardvar = False
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'a\' release':
                        motor_state_mutex.acquire()
                        try:
                            leftvar = False
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'s\' release':
                        motor_state_mutex.acquire()
                        try:
                            backwardvar = False
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
                    elif decoded_data == '\'d\' release':
                        motor_state_mutex.acquire()
                        try:
                            rightvar = False
                        finally:
                            motor_state_mutex.release()
                        print(decoded_data)
            except socket.timeout:
                    print("Client timed out...")
                    motor_state_mutex.acquire()
                    try:
                        close_socket = True
                    finally:
                        motor_state_mutex.release()
                    break
            except Exception as e:
                if exit_program:
                    print(type(e), e)
                    print("Exiting server program...")
                    break
                else:
                    print(type(e), e)
                    pass

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def start_server():
    ip_address = get_ip_address('wlan0') # assumes wlan0 connects to router
    port = 6678
    print "Listening on ip:", ip_address, "port:", port

    # for remote debugging
    #debugpy.listen(('0.0.0.0', 5678))
    #debugpy.wait_for_client()

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
motor_state_mutex = Lock()

start_server()