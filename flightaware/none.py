#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import sys
import time
import dothat.lcd as lcd
import dothat.backlight as backlight

lcd.clear()
backlight.graph_off()
backlight.off()
backlight.update()
