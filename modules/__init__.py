# !/usr/bin/python

import os

ignore = {'__pycache__', '__init__.py', 'citizens'}
list = [x for x in os.listdir(os.path.dirname(os.path.abspath(__file__))) if x not in ignore]
