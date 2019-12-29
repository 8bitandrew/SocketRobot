import socket
import os
import signal
import RPi.GPIO as gpio
from time import sleep

def init_or_clear():
    gpio.setmode(gpio.BOARD)
    gpio.setup(7, gpio.OUT)
    gpio.output(7, False)
    gpio.setup(11, gpio.OUT)
    gpio.output(11, False)
    gpio.setup(40, gpio.OUT)
    gpio.output(40, False)
    gpio.setup(15, gpio.OUT)
    gpio.output(15, False)

prev_forwardstate = 0
prev_backwardstate = 0
prev_leftstate = 0
prev_rightstate = 0

forward = 0
backward = 0
left = 0
right = 0
exit_program = 0

thread = os.fork()

if thread > 0: #Parent process
    init_or_clear()
    while True:
        if prev_forwardstate == forward and prev_backwardstate == backward and prev_leftstate == left and prev_rightstate == right:
            continue
        elif forward == 1 and backward == 0:
            init_or_clear()
            gpio.output(7, False)
            gpio.output(11, True)
            gpio.output(40, False)
            gpio.output(15, True)
        elif backward == 1 and forward == 0:
            init_or_clear()
            gpio.output(7, True)
            gpio.output(11, False)
            gpio.output(40, True)
            gpio.output(15, False)
        else:
            init_or_clear()
else: #Child process
    #message = 'Send message to client.'
    #message = message.encode()

    #socket.setdefaulttimeout(10)
    server = socket.socket()

    server.bind(("10.0.1.15", 6678))

    server.listen(4)
    
        #try:
    client_socket, client_address = server.accept()
    #except socket.timeout:
        #server.close()
        #print("Server timeout. Exiting..")
        #os._exit(1)

    print(client_address, "has connected")

    while True:
        
        received_data = client_socket.recv(1024)
        #client_socket.send(message)
        decoded_data = received_data.decode()
        
        if decoded_data == 'w press':
            forward = 1
            print(decoded_data)
        elif decoded_data == 'w release':
            forward = 0
            print(decoded_data)
        elif decoded_data == 's press':
            backward = 1
            print(decoded_data)
        elif decoded_data == 's release':
            backward = 0
            print(decoded_data)
        else:
            print('Not recognized keypress: %s' % decoded_data)
        
    client_socket.close()
    server.close()
