#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bramkaplay import *


Play = BramkaPlay('<login>', '<password>')      # login example: 505123456
Play.sendsms('<recipient>', '<text message>')   # recipient example: 505123456
