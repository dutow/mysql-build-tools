import os
import sys
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mbt import mbt_command

mbt_command()
