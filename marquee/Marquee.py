#!/usr/bin/env python3

""""
Marquee - a marquee programme for PicoClusters and Blinkt! using Raspberry Pis
David Walker (c) 2017 Data Management & Warehousing
"""

# Library Imports
import random
import re
import time
import socket
from subprocess import call
# Need to install from https://pypi.python.org/pypi/webcolors/1.3 for this import
from webcolors import name_to_rgb

# Global static values

# Define the arrangement of the lamps
STACKS = 4
ROWS = 5
LAMPS = 8

# Define the default log level
LOGLEVEL = 1

# Main
def main():
    "Main Function"

    # Initialize variables and set defaults

    # Status flags
    exitflag = 0

    # Output array
    output = MarqueeDisplay()

    # Define background and foreground colours
    bgcolour = MarqueeColour()
    fgcolour = MarqueeColour()
    if len(bgcolour.rgb) == 0:
        bgcolour.set("black")
    if len(fgcolour.rgb) == 0:
        fgcolour.set("white")

    # Define the host array
    hosts = MarqueeHosts()
    hosts.opensocket()

    # Enter main loop
    print("Type '[help]' for instructions")
    while True:
        string = input("Command: ")

        if len(output.element[0]) <= ROWS * STACKS:
            output.add(character("Padding", bgcolour.rgb, fgcolour.rgb))

        # Process input
        while len(string) > 0:

            # Handle any commands/options
            if string[0] == "[":
                position = string.find("]")
                if position > -1:
                    exitflag = optionprocessor(hosts, string[1:position], fgcolour, bgcolour)
                else:
                    marquelog(1, "Unmatched '[' ")
                    break
                position = position + 1

            # Handle text to display
            else:
                output.add(character(string[0], bgcolour.rgb, fgcolour.rgb))
                output.add(character("Seperator", bgcolour.rgb, fgcolour.rgb))
                position = 1
            string = string[position:]

        if len(output.element[0]) == ROWS * STACKS:
            output.add(character("Padding", bgcolour.rgb, fgcolour.rgb))

        # Send output to devices
        # showlocal(output)
        showblinkt(hosts, output)
        if exitflag:
            break

    # Close the connections
    hosts.closesocket()

    # And exit
    print("Programme terminated successfully")
    return 0

def optionprocessor(hosts, options, fgcolour, bgcolour):
    "Process options inside []"

    # Split up multiple options (delimited by ;)
    for word in options.split(";"):

        # Split up the key from the value (deliited by ':')
        i = word.find(":")
        if i > -1:
            key = word[:i].lower()
            value = word[i+1:]
        else:
            key = word.lower()
            value = ""

        # Now handle each of the keys
        if key == "help":
            showhelp()
        elif key == "exit":
            return 1
        elif key == "shutdown":
            hosts.broadcast("shutdown")
            marquelog(3, "Shutdown sent to all clients")
            return 1
        elif key == "off":
            hosts.broadcast("off")
        elif (key == "fg") or (key == "foreground"):
            marquelog(3, "Setting foreground colour")
            fgcolour.set(value)
        elif (key == "bg") or (key == "background"):
            marquelog(3, "Setting background colour")
            bgcolour.set(value)
        elif (key == "sleep") or (key == "sleeptime"):
            MarqueeSleepTime().set(value)
        else:
            marquelog(1, "Unknown command [" + key + "]")
        return 0

def showlocal(display_string):
    "This displays the message locally as a simulation of the lights"

    # Iterate over the output array and get each lamp array
    for _ in range(0, len(display_string.element[0])-STACKS*LAMPS):

        # Clear screen - Un*x derivatives only
        call("clear")

        # Decompose output and map to lamp positions
        for row in range(0, ROWS):
            msgdata = "|"
            for stack in range(0, STACKS):
                lights = display_string.element[row][stack*LAMPS:stack*LAMPS+LAMPS]
                for light in range(0, LAMPS):
                    (red, green, blue) = lights[light]
                    if red + green + blue > 0:
                        msgdata += "*"
                    else:
                        msgdata += "."
                msgdata += "|"
            print(msgdata)
        time.sleep(MarqueeSleepTime.seconds)

        for row in range(0, ROWS):
            del display_string.element[row][0]

    return 0

def showblinkt(hosts, display_string):
    "This uses UDP to send messages to remote Blinkt! hosts"
    # Iterate over the output array and get each lamp array
    for _ in range(0, len(display_string.element[0])-STACKS*LAMPS):

        # Decompose output and map to lamp positions
        for row in range(0, ROWS):
            for stack in range(0, STACKS):
                rev_lights = []
                rev_stack = STACKS-stack-1
                # Build the messages to send to the Blinkt! here
                lights = display_string.element[row][rev_stack*LAMPS:rev_stack*LAMPS+LAMPS]
                for bulb in range(0,len(lights)):
                    rev_lights.append(lights[len(lights)-bulb-1])
                blinktdata = "set,"
                for light in range(0, LAMPS):
                    (red, green, blue) = rev_lights[light]
                    blinktdata += str(light) + "," + str(red) + "," + str(green) + "," + str(blue)
                    if light < LAMPS - 1:
                        blinktdata += ","
                marquelog(3, "Stack:" + str(stack) + " host: " + str(hosts.addr[stack][row]) + \
                    " Row: " + str(row) + " blinktdata: " + blinktdata)
                hosts.transmit(blinktdata, row, stack)

        # Show lights and sleep
        hosts.broadcast("show")
        time.sleep(MarqueeSleepTime.seconds)

        for row in range(0, ROWS):
            del display_string.element[row][0]

    return 0

def marquelog(severity, message):
    "Display a message"

    if severity <= LOGLEVEL:
        if severity == 1:
            print("ERROR: ", message)
        elif severity == 2:
            print("WARNING: ", message)
        else:
            print("INFO: ", message)
    return 0


def character(letter, bgcolour, fgcolour):
    "Get the lamp array for a particular character"

    # Define the output array
    chararray = [[], [], [], [], []]
    pattern = MarqueeFont().pixels(letter)
    for row in range(0, ROWS):
        for pixel in pattern[row]:
            if pixel:
                chararray[row].append(fgcolour)
            else:
                chararray[row].append(bgcolour)
    return chararray

class MarqueeColour(object):
    "Manage colour selection"

    rgb = ()

    def set(self, name):
        "Set the colour scheme up"

        # Handle a request for a random colour
        if name == "random":
            self.rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            marquelog(3, "Random colour selected: " + str(self.rgb))
            return self.rgb

        # Try and get an rgb sequence from a name
        try:
            self.rgb = name_to_rgb(name)
            marquelog(3, "Colour " + name + " " + str(self.rgb) + " selected")
            return 0
        except ValueError:
            # Define RGB RegEx
            regexp = r"(\d+),\s*(\d+),\s*(\d+)"
            # Try to handle an RGB sequence
            try:
                re.match(regexp, name).group()
                if all(0 <= int(group) <= 255 for group in re.match(regexp, name).groups()):
                    (red, green, blue) = (re.match(regexp, name).groups())
                    marquelog(3, "Colour set to " + str(self.rgb))
                    self.rgb = (int(red), int(green), int(blue))
                    return 0
                else:
                    marquelog(1, "RGB colour out of range (0-255, 0-255, 0-255)")
            except AttributeError:
                marquelog(1, "Colour is not a comma seperated RGB triplet")

        marquelog(1, "Unknown colour " + name + ", setting colour to white")

        # Give up and return white
        self.rgb = (255, 255, 255)

    def show(self):
        "Show the rgb value"
        print(self.rgb)

class MarqueeSleepTime(object):
    "Manage the sleep time between steps"

    seconds = 0.1

    def show(self):
        "Show the sleep time"
        print(self.seconds)

    def set(self, newseconds):
        "Set the time to sleep between each movement"
        try:
            self.seconds = float(newseconds)
            marquelog(3, "Sleep time set to "+newseconds)
        except ValueError:
            marquelog(1, "Can't convert '"+newseconds+"' to a time")

class MarqueeHosts(object):
    "This defines the list of blinkt! hosts in the cluster and their position [stack, row]"

    udpport = 13000
    udpport_sender = 13001

    addr = []
    for stack in range(0, STACKS):
        addr.append([])
    addr[0].append(("192.168.254.11", udpport))
    addr[0].append(("192.168.254.12", udpport))
    addr[0].append(("192.168.254.13", udpport))
    addr[0].append(("192.168.254.14", udpport))
    addr[0].append(("192.168.254.15", udpport))
    addr[1].append(("192.168.254.21", udpport))
    addr[1].append(("192.168.254.22", udpport))
    addr[1].append(("192.168.254.23", udpport))
    addr[1].append(("192.168.254.24", udpport))
    addr[1].append(("192.168.254.25", udpport))
    addr[2].append(("192.168.254.31", udpport))
    addr[2].append(("192.168.254.32", udpport))
    addr[2].append(("192.168.254.33", udpport))
    addr[2].append(("192.168.254.34", udpport))
    addr[2].append(("192.168.254.35", udpport))
    addr[3].append(("192.168.254.41", udpport))
    addr[3].append(("192.168.254.42", udpport))
    addr[3].append(("192.168.254.43", udpport))
    addr[3].append(("192.168.254.44", udpport))
    addr[3].append(("192.168.254.45", udpport))

    testaddr = ("192.168.254.11", udpport)

    broadcastaddr = ("192.168.254.255", udpport)

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
        self.socket.setblocking(False)
        # Accept Connections on port
        self.socket.bind(("", self.udpport_sender))

    def closesocket(self):
        "Close a socket"

        self.socket.close()

    def transmit(self, data, row, stack):
        "Message a single node"

        #if (row == 0) and (stack == 0):
        self.socket.sendto(bytearray(data, "UTF-8"), self.addr[stack][row])
        #self.socket.sendto(bytearray(data, "UTF-8"), self.testaddr)

    def broadcast(self, data):
        "Broadcast to all nodes"

        self.socket.sendto(bytearray(data, "UTF-8"), self.broadcastaddr)

class MarqueeDisplay(object):
    "Add data to the output"

    element = [[], [], [], [], []]

    def add(self, data):
        "Merge a lamp array into the main output"
        for row in range(0, ROWS):
            self.element[row].extend(data[row])
        return self.element

    def show(self):
        "Show element data"
        print(self.element)

class MarqueeFont(object):
    "Define the font Letters"

    # This defines all the characters available in the font
    # Define each of the charachters in the font
    # Based on http://www.fontriver.com/i/fonts/5x5_dots/5x5dots_map.jpg
    letter = {}

    # Build special characters
    letter["Seperator"] = [[], [], [], [], []]
    letter["Block"] = [[], [], [], [], []]
    letter["Padding"] = [[], [], [], [], []]
    for row in range(0, ROWS):
        letter["Seperator"][row].append(0)
        for width in range(0, ROWS):
            letter["Block"][row].append(1)
        for stack in range(0, STACKS*LAMPS):
            letter["Padding"][row].append(0)

    # Build standard characters
    letter[" "] = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], \
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    letter["!"] = [[0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]
    letter["\""] = [[0, 1, 0, 1, 0], [0, 1, 0, 1, 0], [0, 0, 0, 0, 0], \
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    letter["#"] = [[0, 1, 0, 1, 0], [1, 1, 1, 1, 1], [0, 1, 0, 1, 0], \
        [1, 1, 1, 1, 1], [0, 1, 0, 1, 0]]
    letter["$"] = [[0, 1, 1, 1, 1], [1, 0, 1, 0, 0], [0, 1, 1, 1, 0], \
        [0, 0, 1, 0, 1], [1, 1, 1, 1, 0]]
    letter["%"] = [[1, 0, 0, 0, 1], [0, 0, 0, 1, 0], [0, 0, 1, 0, 0], \
        [0, 1, 0, 0, 0], [1, 0, 0, 0, 1]]
    letter["&"] = [[0, 1, 1, 0, 0], [1, 0, 0, 1, 0], [0, 1, 1, 1, 1], \
        [1, 0, 0, 1, 0], [0, 1, 1, 1, 1]]
    letter["'"] = [[0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0], \
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    letter["("] = [[0, 0, 0, 1, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 0, 0, 1, 0]]
    letter[")"] = [[0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 1, 0, 0, 0]]
    letter["*"] = [[0, 0, 1, 0, 0], [1, 0, 1, 0, 1], [0, 1, 1, 1, 0], \
        [1, 0, 1, 0, 1], [0, 0, 1, 0, 0]]
    letter["+"] = [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 1, 1, 1, 0], \
        [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]]
    letter["."] = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]
    letter["-"] = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 1, 1, 1, 0], \
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    letter[","] = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], \
        [0, 0, 0, 1, 0], [0, 0, 1, 0, 0]]
    letter["/"] = [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 0, 1, 0], [0, 0, 0, 0, 1]]
    letter["0"] = [[0, 1, 1, 1, 0], [1, 0, 0, 1, 1], [1, 0, 1, 0, 1], \
        [1, 1, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["1"] = [[0, 0, 1, 0, 0], [0, 1, 1, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 1, 1, 1, 0]]
    letter["2"] = [[1, 1, 1, 1, 0], [0, 0, 0, 0, 1], [0, 1, 1, 1, 0], \
        [1, 0, 0, 0, 0], [1, 1, 1, 1, 1]]
    letter["3"] = [[1, 1, 1, 1, 0], [0, 0, 0, 0, 1], [0, 0, 1, 1, 0], \
        [0, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["4"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [0, 1, 1, 1, 1], \
        [0, 0, 0, 0, 1], [0, 0, 0, 0, 1]]
    letter["5"] = [[1, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 0], \
        [0, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["6"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 0], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["7"] = [[1, 1, 1, 1, 1], [0, 0, 0, 0, 1], [0, 0, 0, 1, 0], \
        [0, 0, 0, 1, 0], [0, 0, 0, 1, 0]]
    letter["8"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [0, 1, 1, 1, 0], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["9"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [0, 1, 1, 1, 1], \
        [0, 0, 0, 0, 1], [0, 0, 1, 1, 0]]
    letter[":"] = [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0], \
        [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]]
    letter[";"] = [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0], \
        [0, 0, 1, 0, 0], [0, 1, 0, 0, 0]]
    letter["<"] = [[0, 0, 0, 1, 0], [0, 0, 1, 0, 0], [0, 1, 0, 0, 0], \
        [0, 0, 1, 0, 0], [0, 0, 0, 1, 0]]
    letter["="] = [[0, 0, 0, 0, 0], [0, 1, 1, 1, 0], [0, 0, 0, 0, 0], \
        [0, 1, 1, 1, 0], [0, 0, 0, 0, 0]]
    letter[">"] = [[0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], \
        [0, 0, 1, 0, 0], [0, 1, 0, 0, 0]]
    letter["?"] = [[0, 1, 1, 1, 0], [0, 0, 0, 1, 0], [0, 0, 1, 1, 0], \
        [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]
    letter["@"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 1, 0, 1], \
        [1, 0, 0, 1, 1], [0, 1, 1, 0, 0]]
    letter["A"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["B"] = [[1, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 0], \
        [1, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["C"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 0, 0, 0, 0], \
        [1, 0, 0, 0, 0], [0, 1, 1, 1, 1]]
    letter["D"] = [[1, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["E"] = [[1, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 0], \
        [1, 0, 0, 0, 0], [1, 1, 1, 1, 1]]
    letter["F"] = [[1, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 1, 1, 0, 0], \
        [1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]
    letter["G"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 0, 1, 1, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 1]]
    letter["H"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["I"] = [[0, 1, 1, 1, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 1, 1, 1, 0]]
    letter["J"] = [[0, 0, 1, 1, 1], [0, 0, 0, 0, 1], [0, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["K"] = [[1, 0, 0, 1, 0], [1, 0, 1, 0, 0], [1, 1, 1, 0, 0], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["L"] = [[1, 0, 0, 0, 0], [1, 0, 0, 0, 0], [1, 0, 0, 0, 0], \
        [1, 0, 0, 0, 0], [1, 1, 1, 1, 1]]
    letter["M"] = [[1, 0, 0, 0, 1], [1, 1, 0, 1, 1], [1, 0, 1, 0, 1], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["N"] = [[1, 1, 0, 0, 1], [1, 0, 1, 0, 1], [1, 0, 1, 0, 1], \
        [1, 0, 1, 0, 1], [1, 0, 0, 1, 1]]
    letter["O"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["P"] = [[1, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 0], \
        [1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]
    letter["Q"] = [[0, 1, 1, 0, 0], [1, 0, 0, 1, 0], [1, 0, 0, 1, 0], \
        [1, 0, 0, 1, 0], [0, 1, 1, 1, 1]]
    letter["R"] = [[1, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 0], \
        [1, 0, 0, 1, 0], [1, 0, 0, 0, 1]]
    letter["S"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 0], [0, 1, 1, 1, 0], \
        [0, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["T"] = [[1, 1, 1, 1, 1], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 0, 1, 0, 0]]
    letter["U"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["V"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [0, 1, 0, 1, 0], \
        [0, 1, 0, 1, 0], [0, 0, 1, 0, 0]]
    letter["W"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 0, 1, 0, 1], \
        [1, 1, 0, 1, 1], [1, 0, 0, 0, 1]]
    letter["X"] = [[1, 0, 0, 0, 1], [0, 1, 0, 1, 0], [0, 0, 1, 0, 0], \
        [0, 1, 0, 1, 0], [1, 0, 0, 0, 1]]
    letter["Y"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [0, 1, 1, 1, 0], \
        [0, 0, 1, 0, 0], [0, 0, 1, 0, 0]]
    letter["Z"] = [[1, 1, 1, 1, 1], [0, 0, 0, 0, 1], [0, 1, 1, 1, 0], \
        [1, 0, 0, 0, 0], [1, 1, 1, 1, 1]]
    letter["\\"] = [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 0, 1, 0], [0, 0, 0, 0, 1]]
    letter["^"] = [[0, 0, 1, 0, 0], [0, 1, 0, 1, 0], [0, 0, 0, 0, 0], \
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    letter["a"] = [[1, 1, 1, 1, 0], [0, 0, 0, 0, 1], [0, 1, 1, 1, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 1]]
    letter["b"] = [[1, 0, 0, 0, 0], [1, 1, 1, 1, 0], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["c"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 0, 0, 0], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["d"] = [[0, 0, 0, 0, 1], [0, 1, 1, 1, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 1]]
    letter["e"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1], \
        [1, 0, 0, 0, 0], [0, 1, 1, 1, 1]]
    letter["f"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 0], [1, 1, 1, 0, 0], \
        [1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]
    letter["g"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [0, 1, 1, 1, 1], \
        [0, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["h"] = [[1, 0, 0, 0, 0], [1, 1, 1, 1, 0], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["i"] = [[0, 0, 1, 0, 0], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 0, 1, 0, 0]]
    letter["j"] = [[0, 0, 1, 0, 0], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0], \
        [0, 0, 1, 0, 0], [0, 1, 1, 0, 0]]
    letter["k"] = [[1, 0, 0, 0, 1], [1, 0, 0, 1, 0], [1, 1, 1, 0, 0], \
        [1, 0, 0, 1, 0], [1, 0, 0, 0, 1]]
    letter["l"] = [[1, 0, 0, 0, 0], [1, 0, 0, 0, 0], [1, 0, 0, 0, 0], \
        [1, 0, 0, 0, 0], [0, 1, 1, 1, 1]]
    letter["m"] = [[0, 1, 0, 1, 0], [1, 0, 1, 0, 1], [1, 0, 1, 0, 1], \
        [1, 0, 1, 0, 1], [1, 0, 1, 0, 1]]
    letter["n"] = [[1, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["o"] = [[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["p"] = [[1, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 1, 1, 1, 0], [1, 0, 0, 0, 0]]
    letter["q"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [0, 1, 1, 1, 1], [0, 0, 0, 0, 1]]
    letter["r"] = [[1, 0, 1, 1, 0], [1, 1, 0, 0, 1], [1, 0, 0, 0, 0], \
        [1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]
    letter["s"] = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 0], [0, 1, 1, 1, 0], \
        [0, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["t"] = [[1, 0, 0, 0, 0], [1, 1, 1, 0, 0], [1, 0, 0, 0, 0], \
        [1, 0, 0, 0, 1], [0, 1, 1, 1, 0]]
    letter["u"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], \
        [1, 0, 0, 1, 1], [0, 1, 1, 0, 1]]
    letter["v"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [0, 1, 0, 1, 0], \
        [0, 1, 0, 1, 0], [0, 0, 1, 0, 0]]
    letter["w"] = [[1, 0, 1, 0, 1], [1, 0, 1, 0, 1], [1, 0, 1, 0, 1], \
        [1, 0, 1, 0, 1], [0, 1, 0, 1, 0]]
    letter["x"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [0, 1, 1, 1, 0], \
        [1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]
    letter["y"] = [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [0, 1, 1, 1, 1], \
        [0, 0, 0, 0, 1], [1, 1, 1, 1, 0]]
    letter["z"] = [[1, 1, 1, 1, 1], [0, 0, 0, 1, 0], [0, 0, 1, 0, 0], \
        [0, 1, 0, 0, 0], [1, 1, 1, 1, 1]]

    def pixels(self, data):
        "Find a letter in the font or replace with a block"

        if data in list(self.letter):
            return self.letter[data]
        else:
            return self.letter["Block"]

    def show(self):
        "Display the letters"

        print(self.letter)

def showhelp():
    "Show the help text when requested"
    print("")
    print("Marquee by David Walker - Help Text")
    print("")
    print("Overview")
    print("========")
    print("All commands are placed between square brackets '[]' and are case insensitive")
    print("    e.g. [help] or [Help]")
    print("Commands with parameters are seperated by colons ':' e.g. [fg:red]")
    print("Multiple commands can be in one pair of brackets seperated by semi-colons ';'")
    print("    e.g. [fg:red;bg:black]")
    print("")
    print("Commands")
    print("========")
    print("[bg:colourname] or [background:colourname] sets the foreground colour to the")
    print("    colourname (see below).")
    print("[exit] will stop the control program but allow clients to continue running.")
    print("    Restarting the control program will allow new commands to be entered.")
    print("[fg:colourname] or [foreground:colourname] sets the foreground colour to the")
    print("    colourname (see below).")
    print("[help] displays this message.")
    print("[off] tells all clients to turn off their lights")
    print("[shutdown] will stop the control program and all clients.")
    print("[sleep:decimal] or [sleeptime:decimal] sets the number of seconds between pixel")
    print("    moves (default = 0.1).")
    print("")
    print("Colour Names")
    print("============")
    print("Colour Names are normally a decimal RGB triplet e.g. 50, 100, 150 where each value")
    print("    is between 0 and 255.")
    print("Colour Names can also be CSS3 compliant names e.g. 'Red' which converts to '255, 0, 0'.")
    print("    Colour Names are case insensitive.")
    print("Marquee supports a special colour name 'random'.")
    print("    Random sets the colours to a random colour.")
    print("")
    return 0

if __name__ == "__main__":
    main()
