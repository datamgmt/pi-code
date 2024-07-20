#!/usr/bin/env python
# -*- coding: utf-8 -*-

def value_exists_in_file(value, filename='data.txt'):
    try:
        with open(filename, 'r') as file:
            for line in file:
                if line.strip() == value:
                    return True
        return False
    except FileNotFoundError:
        print(f'The file {filename} does not exist.')
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python check_value.py <value_to_check>')
        sys.exit(2)

    value_to_check = sys.argv[1]
    filename = '/home/pi/pi-code/flightaware/aircraft.txt'

    if value_exists_in_file(value_to_check, filename):
        print('1', end='')
    else:
        print('0', end='')
        
