#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

def value_exists_in_file(value, filename='data.txt'):
    try:
        with open(filename, 'r') as file:
            for line in file:
                if line.strip() == value:
                    return True
        return False
    except FileNotFoundError:
        print(f"The file {filename} does not exist.")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python check_value.py <value_to_check>")
        sys.exit(2)

    value_to_check = sys.argv[1]
    filename = '/Users/datamgmt/Documents/GitHub/pi-code/flightaware/aircraft.txt'

    if value_exists_in_file(value_to_check, filename):
        #print(f"The value '{value_to_check}' exists in the file '{filename}'.")
        print("1")
        sys.exit(1)
    else:
        #print(f"The value '{value_to_check}' does not exist in the file '{filename}'.")
        print("0")
        sys.exit(0)

