import Tkinter, tkFileDialog
import ttk
import tkMessageBox
import labrad
from twisted.internet.error import ConnectionRefusedError
import sys
import yaml
import copy
from math import * #so we can use sin, cos, etc
from qubit_interface import *

    
if __name__ == "__main__":
    gui = Interface() #make the interface
    gui.root.mainloop() #set everything in motion

