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

  #the following functions will come in useful when evaluating code in code frame
  def setValue(nameString, newValue):
    """Sets the value of the ViewValue named nameString to newValue."""
    gui.setValue(nameString, newValue)
    
  def setTime(nameString, newTime):
    """Sets the time of the ViewTime name nameString to newTime."""
    gui.setTime(nameString, newTime)
    
  def addTime(name, time):
    """Makes and adds a ViewTime with the the given name and time."""
    gui.addTime(name=name, time=time)
    
  def deleteTime(name):
    """Deletes the ViewTime with the given name."""
    gui.deleteTime(name=name)
    
  def setDurationValue(traceName, durationName, valueName):
    """Sets the assocViewValue of the ViewDuration named durationName, in the trace name traceName, to the ViewValue named valueName."""
    trace = gui.traceNamed(traceName)
    duration = trace.durationNamed(durationName)
    value = gui.valueNamed(valueName)
    duration.setViewValue(value)
    
  def mergeValues(valueNameA, valueNameB):
    """Merges the two named ViewValues."""
    valueA = gui.valueNamed(valueNameA)
    valueB = gui.valueNamed(valueNameB)
    valueB.merge(valueA)
    
  def setDurationName(traceName, startTimeName, newDurationName):
    """Sets the name of the ViewDuration with the startTime named startTimeName, in the trace named traceName, to newDurationName."""
    trace = gui.traceNamed(traceName)
    time = gui.timeNamed(startTimeName)
    trace.durationStartingAt(time).setName(newDurationName)
    
  def setValueFunction(nameString, functionString):
    """Sets the function for the ViewValue named nameString to the function given by functionString."""
    gui.valueNamed(nameString).setFunction(functionString)
    
  gui.root.mainloop() #set everything in motion

