import socket, threading, struct, fcntl, debugpy
import RPi.GPIO as gpio
from enum import Enum
from multiprocessing import Lock

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
    
    def interpret_state(self, forwardvar, backwardvar, leftvar, rightvar):
        x_state = (leftvar and not rightvar) or (rightvar and not leftvar)
        y_state = (forwardvar and not backwardvar) or (backwardvar and not forwardvar)
        state_to_set = self.State.NONE.value
        secondary_state_to_set = False

        if x_state and y_state:
            if self.secondary_state_exists:
                state_to_set = self.current_state
                secondary_state_to_set = self.secondary_state_exists
            else:
                secondary_state_to_set = True
                if forwardvar and self.State.FORWARD.value != self.current_state:
                    state_to_set = self.State.FORWARD.value
                elif backwardvar and self.State.BACKWARD.value != self.current_state:
                    state_to_set = self.State.BACKWARD.value
                elif leftvar and self.State.LEFT.value != self.current_state:
                    state_to_set = self.State.LEFT.value
                elif rightvar and self.State.RIGHT.value != self.current_state:
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

        self.secondary_state_exists = secondary_state_to_set
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
        global forwardvar
        global backwardvar
        global leftvar
        global rightvar
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
                with motor_state_mutex:
                    forwardvar = False
                    backwardvar = False
                    leftvar = False
                    rightvar = False
                    close_socket = False
            
            with motor_state_mutex:
                new_state = self.interpret_state(forwardvar, backwardvar, leftvar, rightvar)
                self.set_state(new_state)

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

        #socket.setdefaulttimeout(300) # seconds
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
                        with motor_state_mutex:
                            close_socket = True
                        print(client_address, "disconnected")
                        break
                    elif decoded_data == 'exit':
                        client_socket.close()
                        with motor_state_mutex:
                            exit_program = True
                        print(decoded_data)
                        break
                    elif decoded_data == '\'w\' press':
                        with motor_state_mutex:
                            forwardvar = True
                        print(decoded_data)
                    elif decoded_data == '\'a\' press':
                        with motor_state_mutex:
                            leftvar = True
                        print(decoded_data)
                    elif decoded_data == '\'s\' press':
                        with motor_state_mutex:
                            backwardvar = True
                        print(decoded_data)
                    elif decoded_data == '\'d\' press':
                        with motor_state_mutex:
                            rightvar = True
                        print(decoded_data)
                    elif decoded_data == '\'w\' release':
                        with motor_state_mutex:
                            forwardvar = False
                        print(decoded_data)
                    elif decoded_data == '\'a\' release':
                        with motor_state_mutex:
                            leftvar = False
                        print(decoded_data)
                    elif decoded_data == '\'s\' release':
                        with motor_state_mutex:
                            backwardvar = False
                        print(decoded_data)
                    elif decoded_data == '\'d\' release':
                        with motor_state_mutex:
                            rightvar = False
                        print(decoded_data)
            except socket.timeout:
                    print(client_address, "timed out...")
                    with motor_state_mutex:
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

def get_ip(iface = 'wlan0'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = struct.pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

def start_server():
    ip_address = get_ip() # assumes wlan0 connects to router
    port = 6678
    print("Listening on ip:", ip_address, "port:", port)

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