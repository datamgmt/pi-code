#!/usr/bin/env python3

"""
Receiver for Marquee programme on PicoClusters and Blinkt! using Raspberry Pis
David Walker (c) 2017 Data Management & Warehousing
"""

# Global static values

BUFFER = 1024

# Library Imports
import socket
# Need to install from Pimoroni for this import
import blinkt

# Main
def main():
   "Mail Function"

   hosts = MarqueHosts()
   hosts.opensocket()

   # Set Blinkt! brightness
   blinkt.set_brightness(0.1)

   # Enter main loop
   print ("Waiting to receive messages ...")
   while True:
      # Receive packet
      (data,addr) = hosts.receive()

      # Split up string into data points
      message = list(data.decode('utf-8').split(','))

      # Get the action from the first position
      action = message[0]
      del message[0]

      # Process actions

      if action == 'set':
         print('set')

         # For each lamp
         for i in range(8):
            # Set the RGB number
           blinkt.set_pixel(int(message[i*4]), int(message[i*4+1]), int(message[i*4+2]), int(message[i*4+3]))

      elif action == 'show':
         print('show')
         blinkt.show()

      elif action == 'shutdown':
         print('shutdown')
         break

      else:
         print("Unknown command received: " + BlinktCommand)

   # Close the connections
   hosts.closesocket()

   return 0

class MarqueHosts(object):
    "This defines the list of blinkt! hosts in the cluster and their position [stack, row]"

    udpport = 13000

    addr = []

    testaddr = ("192.168.1.3", udpport)

    broadcastaddr = ("192.168.1.255", udpport)

    socket = None

    def opensocket(self):
        "Open a socket"

        # Create Datagram Socket (UDP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Make Socket Reusable
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Allow incoming broadcasts
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set socket to non-blocking mode
        #self.socket.setblocking(False)
        # Accept Connections on port
        self.socket.bind(("", self.udpport))

    def closesocket(self):
        "Close a socket"

        self.socket.close()

    def transmit(self, data, row, stack):
        "Message a single node"

        self.socket.sendto(bytearray(data, "UTF-8"), self.addr[stack][row])
        self.socket.sendto(bytearray(data, "UTF-8"), self.testaddr)

    def receive(self):
        return self.socket.recvfrom(BUFFER)

    def broadcast(self, data):
        "Broadcast to all nodes"

        self.socket.sendto(bytearray(data, "UTF-8"), self.broadcastaddr)

if __name__ == "__main__":
    main()
