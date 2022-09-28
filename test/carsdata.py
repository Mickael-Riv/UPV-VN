import os, sys
import time
import struct

name = str(sys.argv[1])
id = name[:-1]
import socket


def listen():
  """
  It listens for ICMP packets on port 7, and if it receives one, it writes the IP address of the
  sender to a file
  """
  s = socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_ICMP)
  s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)  
  s.settimeout(10)
  val = 0
  sequence = 0
  while sequence < 8096:
    print(val)
    try:
      data, addr = s.recvfrom(1508)
    except socket.timeout:
      break

    if data != None :
# Getting the ICMP header from the packet and then it is unpacking it.
      icmp_header = data[20:28]
      type, code, checksum, p_id, sequence = struct.unpack('bbHHh', icmp_header)
      if sequence != 256:
        fichier = open("./vehicle/"+name+".txt", "w")
        fichier.write(str(addr) + " " + str(val) + " sequence: " + str(sequence))
        fichier.close()

  s.close()
  try:
    fichier = open("./vehicle/"+name+".txt", "w")
    fichier.write("")
    fichier.close()
  except:
    pass
        #fichier = open("./vehicle/"+name+".txt", "w")
        #fichier.write("")
        #fichier.close()
  #data = None

listen()