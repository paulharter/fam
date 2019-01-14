import os
import json

try:
    from .config_local import *
except ImportError as e:
    print("you have to add a config_local.py file")

