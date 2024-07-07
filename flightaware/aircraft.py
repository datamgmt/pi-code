#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import sys
import time
import dothat.lcd as lcd
import dothat.backlight as backlight

lcd.write(sys.argv[1])
backlight.set_graph(int(sys.argv[2])/6)
backlight.rgb(66,245,233)
backlight.update()
