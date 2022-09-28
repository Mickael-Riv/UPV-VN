from email import message
import socket
import time
import sys

# The above code is sending a message to the broadcast address of the network.
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

# Enable broadcasting mode
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

server.settimeout(0.2)
#while True:
if sys.argv[1] != None:
    for i in (0,3):
        message = bytes('sortie:'+ sys.argv[1], "utf-8")
        server.sendto(message, ('10.0.255.255', 37020))
        print("message sent!")
            #time.sleep(1)
server.close()
