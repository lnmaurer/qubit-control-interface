import Tkinter
import ttk

def find(f, seq):
  """Return first item in sequence where f(item) == True. Returns None if there aren't any such items."""
  for item in seq:
    if f(item): 
      return item

class ViewTime:
  """The class for a time drawn on the trace"""
  def __init__(self, name, time, locked, interface, row=None):
    self.name = name
    self.time = int(round(time)) #only allow integer times
    self.locked = locked
    self.interface = interface
    self.row = row
    
    self.stringVar = Tkinter.StringVar()
    self.stringVar.set(str(self.time))
    self.intVar = Tkinter.IntVar()
    self.intVar.set(1 if self.locked else 0)
    self.tkLabel = None
    self.tkEntry = None
    self.tkCheck = None
  
  def toDict(self):
    """Retrurns a dict that describes this ViewTime. For use in saving the experiment."""
    return {'name': self.name, 'time': self.time, 'locked': self.locked}
  
  def setTime(self, time, errorIfImpossible=False):
    """
    The time of a ViewTime is a time. It can only be set if it isn't locked.
    
    If errorIfImpossible is set to True, the method will throw an error if it can't be set to the requested time.
    """
    if (self.time != time) and (not self.locked):
      sortedTimes =  [t.time for t in self.interface.times]
      sortedTimes.sort()
      index = sortedTimes.index(self.time)
      #find the limits for what this time can be set to. maxTime is the largest time it can be and minTime is the smallest time it can be
      if index == 0: #in this case, self is the smallest time, don't let it move
	if errorIfImpossible:
	  pass #todo: raise error
	else:
	  maxTime = minTime = 0
      elif index == (len(sortedTimes)-1): #in this case, self is the largest time
	minTime = sortedTimes[index-1]
	maxTime = None
      else:
	minTime = sortedTimes[index-1]
	maxTime = sortedTimes[index+1]
	
      if ((maxTime == None) and (time > minTime)) \
	or ((maxTime != None) and (minTime != None) and (time > minTime) and (time < maxTime)):
	self.time = int(round(time)) #can only take integer times
	#since times are on every trace, need to update all of them
	self.interface.redrawAllCanvases()
	self.interface.redrawAllXaxies()
      elif errorIfImpossible: #can't be set to the requested time
	pass #todo: throw an error
    elif (self.time != time) and errorIfImpossible: #can't be set to the requested time because it's locked
	pass #todo: throw an error
	
    #by keeping this outside the previous if statement, the tkEntry is restored to the old time if an unacceptable time was entered
    self.stringVar.set(str(self.time))
  
  def setName(self, name):
    """Sets the time's name and redraws the value frame. The name can only be changed if the time isn't locked."""
    if (self.name != name): #prevents needless refresh if the name hasn't changed
      if (not self.locked) and (name not in [t.name for t in self.interface.times]):
	self.name = name
	self.interface.redrawValueFrame() #the description of any associated durations will have to be redrawn to reflect this time's new name
      else:
	pass #todo: throw an error
  
  def disp(self, row):
    """Draws the widgets associated with this time in the value frame: a label with the name, an entry box with the value, and a checkbox for locking it."""
    self.row = row

    #get rid of old widgets if they exsist
    if self.tkLabel != None:
      self.tkLabel.destroy()
    if self.tkEntry != None:
      self.tkEntry.destroy()
    if self.tkCheck != None:
      self.tkCheck.destroy()
      
    #the label
    self.tkLabel = ttk.Label(self.interface.valueFrame, text=self.name)
    self.tkLabel.grid(column=0, row=row, sticky='w', padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkLabel)
    
    #the entry box
    self.tkEntry = ttk.Entry(self.interface.valueFrame, textvariable=self.stringVar) #todo: get validation working for tkEntry
    self.tkEntry.grid(column=1, row=row, sticky='w', padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkEntry)
    
    self.tkEntry.config(state = 'disabled' if self.locked else 'normal')
    
    #this method updates the time if it's changed in the entry box
    def entryMethod(eventObj):
      if self.tkEntry.get() != '':
	self.setTime(float(self.tkEntry.get()))
      return 1
    self.tkEntry.bind("<Return>",entryMethod)
    
    #the checkbox handles locking the time
    def checkMethod():
      self.locked = (self.intVar.get() == 1)
      self.tkEntry.config(state = 'disabled' if self.locked else 'normal')
      
    self.tkCheck = ttk.Checkbutton(self.interface.valueFrame, text='Locked?', command=checkMethod, variable=self.intVar)
    self.tkCheck.grid(column=2, row=row,sticky='w', padx=5, pady=5)   
    self.interface.valueFrameParts.append(self.tkCheck)
  
  def redraw(self):
    """Redraw the widgets in the value frame in the same row as it was before"""
    if self.row != None:
      self.disp(self.row)
  
  def dragMethod(self, eventObj):
    """Used for changing the time by dragging the line on the canvas"""
    self.setTime(self.interface.xToTime(eventObj.x))
    
  def clickMethod(self, eventObj):
    """Used when the line on the canvas is clicked"""
    iface = self.interface
    if (iface.mode == 'rename'):
      self.setName(iface.nameEntry.get()) #set the name if we're in rename mode
      iface.mode = 'select'
    elif iface.mode == 'select':
      iface.bindCanvasesDrag(self.dragMethod) #allow the line on the canvas to be dragged after it's clicked on
    elif (iface.mode == 'deleteTime') and not self.locked:
      self.interface.deleteTime(viewTime=self)
      iface.mode = 'select' #go back to select mode
  
class ViewValue:
  """The class for a value drawn on the trace"""
  def __init__(self, name, value, locked, interface, functionText='1.0', mode="constant", row=None):
    self.name = name
    self.locked = locked
    self.interface = interface
    self.row = row
    
    #can either be in constant mode -- which allows GUI dragging -- or in function mode, which allows more complicated values but doesn't allow dragging
    self.mode = mode
    self.value = value
    self.functionText = functionText
    self.variables = {} #will hold the variables for the lambda
    if self.mode != 'constant':
      self.makeLambda() #don't run initially because you can run in to trouble when the interface is still being initialized
    
    self.stringVar = Tkinter.StringVar()
    #text we display depends on what mode we're in
    if self.mode == 'constant':
      self.stringVar.set(str(value))
    else:
      self.stringVar.set(functionText)
    self.intVar = Tkinter.IntVar()
    self.intVar.set(1 if self.locked else 0)
    self.tkLabel = None
    self.tkEntry = None
    self.tkCheck = None
    self.tkMenubutton = None

  def toDict(self):
    """Retrurns a dict that describes this ViewValue. For use in saving the experiment."""
    return {'name': self.name, 'value': self.value, 'locked': self.locked, 'functionText': self.functionText, 'mode': self.mode}    
    
  def makeLambda(self, force = False):
    """make a function using the text in self.functionText. If force is True, remakes lambda even if variables are unchanged, which you want to do sometimes (e.g. '1.0' and '5.0' have the same dictionary)"""   
    variables = {'self': self} #dictionary to hold variables
    #look though the variables in interface to see if any of them are used
    #these include any variables made when running the code in the code frame
    #and all the functions/variables from the math libary (e.g. 'sin', 'pi', etc.)
    for globalVariableName in self.interface.variables.keys():
      if globalVariableName in self.functionText: #only add it to the dictionary if it's needed -- note that this isn't foolproof, the text may be in the string even if the function/variable isn't used (e.g. if you use 'ceil()', 'e' will also be added to the dictionary)
	variables[globalVariableName] = self.interface.variables[globalVariableName]
    for time in self.interface.times:
      if time.name in self.functionText: #only add it to the dictionary if it's needed -- same caveat as above
	variables[time.name] = time.time * 1e-9 #add all the times to variables, and make them in nS
    for value in self.interface.values:
      if value.name in self.functionText: #only add it to the dictionary if it's needed -- same caveat as above
	variables[value.name] = value.value #add all the values to variables
    if force or (variables != self.variables): #only exectute if variables have changed since last time or if it's forced
      self.variables = variables.copy()
      #don't have to import math because all those functions will end up in variables
      exec "self.lda = lambda t: " + self.functionText in variables
    
  def function(self, t):
    """returns the value of self.lda for the given t (in seoncds)"""
    self.makeLambda() #need to call in case something has changed. todo: find way to avoid this
    return self.lda(t)
    
  def setFunction(self, string):
    """Sets self.function using the given string. The string should be a function of t (e.g. 'sin(t)'). Note that the value at a given time is the function multipled by self.value"""
    if not self.locked:
      self.functionText = string
      self.makeLambda(force = True)

      #update all the traces which have this value
      self.updateTraces()
    else:
      pass #todo: throw error
    
  def values(self, times):
    """Returns the value this ViewValue takes at the given times. The value this takes at a given time is self.value*self.function(time)"""
    if self.mode == 'constant':
      return len(times)*[self.value]
    else:
      return [self.function(t*1e-9) for t in times] #the 1e-9 coverts the time to nanoseconds
  
  def maxValue(self):
    """Returns the maximum value this takes over the whole period from start to end"""
    if self.mode == 'constant':
      return self.value
    else:
      times = self.interface.timeArray()
      return max(self.values(times))

  def minValue(self):
    """Returns the minimum value this takes over the whole period from start to end"""
    if self.mode == 'constant':
      return self.value
    else:
      times = self.interface.timeArray()
      return min(self.values(times))
      
  def updateTraces(self):
    """Updates all traces this value appears on"""
    for trace in [t for t in self.interface.traces if self in t.values()]:
      trace.redrawCanvas()
      trace.redrawYaxis()
      
  def setValue(self, value, errorIfImpossible=False):
    """
    The value of a ViewValue is a voltage. It can only be set if it isn't locked
        
    If errorIfImpossible is set to True, the method will throw an error if it can't be set to the requested value.
    """
    if (self.value != value) and (not self.locked):
      self.value = value
      
      #update all the traces which have this value
      self.updateTraces()
    elif (self.value != value) and errorIfImpossible: #can't be set to the requested time because it's locked
	pass #todo: throw an error
	
    #by keeping this outside the previous if statement, the tkEntry is restored to the old value if an unacceptable value was entered
    self.stringVar.set(str(value))
	
  def setName(self, name):
    """Sets the value's name and redraws the value frame. The name can only be changed if the value isn't locked."""
    if (self.name != name): #don't needlessly refresh if name hasn't changed
      if (not self.locked) and (name not in [v.name for v in self.interface.values]):
	self.name = name
	self.interface.redrawValueFrame() #the description of any associated durations will have to be redrawn to reflect this value's new name
      else:
	pass #todo: throw error
	
  def merge(self, toMerge):
    """If toMerge is a duration, it takes this for its value. If toMerge is a value, this value is replaced everywhere by toMerge"""
    if isinstance(toMerge, ViewDuration):
      toMerge.assocViewValue = self
    else: #it's a ViewValue
      for duration in self.interface.durations():
	if duration.assocViewValue == self:
	  duration.assocViewValue = toMerge
  
    self.interface.removeUnusedValues() #could be unused values now
    self.interface.refresh()
    
  def disp(self, row):
    """Draws the widgets associated with this value in the value frame: a label with the name, an entry box with the value, and a checkbox for locking it."""
    self.row = row

    #get rid of old widgets if they exsist
    if self.tkLabel != None:
      self.tkLabel.destroy()
    if self.tkEntry != None:
      self.tkEntry.destroy()
    if self.tkCheck != None:
      self.tkCheck.destroy()
    if self.tkMenubutton != None:
      self.tkMenubutton.destroy()
    
    #the label
    self.tkLabel = ttk.Label(self.interface.valueFrame, text=self.name)
    self.tkLabel.grid(column=0, row=row, sticky='w', padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkLabel)
    
    #the entry box
    self.tkEntry = ttk.Entry(self.interface.valueFrame, textvariable=self.stringVar) #todo: get validation working for tkEntry
    self.tkEntry.grid(column=1, row=row,sticky='w', padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkEntry)

    self.tkEntry.config(state = 'disabled' if self.locked else 'normal')

    #this method updates the value if it's changed in the entry box
    def entryMethod(eventObj):
      if self.tkEntry.get() != '':
	if self.mode == "constant":
	  self.setValue(float(self.tkEntry.get()))
	else: #function mode
	  self.setFunction(str(self.tkEntry.get()))
      return 1
    self.tkEntry.bind("<Return>",entryMethod)
    
    #the checkbox handles locking the value
    def checkMethod():
      self.locked = (self.intVar.get() == 1)
      self.tkEntry.config(state = 'disabled' if self.locked else 'normal')
      
    self.tkCheck = ttk.Checkbutton(self.interface.valueFrame, text='Locked?', command=checkMethod, variable=self.intVar)
    self.tkCheck.grid(column=2, row=row,sticky='w', padx=5, pady=5)   
    self.interface.valueFrameParts.append(self.tkCheck)
    
    #the menubutton slects whether this ViewValue takes a constant or a function
    def setConstant():
      self.mode = 'constant'
      self.stringVar.set(str(self.value))
      self.updateTraces()
    
    def setFunction():
      self.mode = 'function'
      self.stringVar.set(str(self.functionText))
      self.makeLambda(force = True)
      self.updateTraces()
      
    
    self.tkMenubutton = ttk.Menubutton(self.interface.valueFrame, text="Type")
    self.tkMenubutton.grid(column=3, row=row,sticky='ew', padx=5, pady=5) 
    menu = Tkinter.Menu(self.tkMenubutton, tearoff = 0)
    self.tkMenubutton["menu"] = menu
    
    #todo: make the selected option depend on self.mode; at present, neither are selected by default
    menu.add_radiobutton(label="Constant", command=setConstant)
    menu.add_radiobutton(label="Function", command=setFunction)
    
    self.interface.valueFrameParts.append(self.tkMenubutton)

    
  def redraw(self):
    """Redraw the widgets in the value frame in the same row as it was before"""
    if self.row != None:
      self.disp(self.row)
  
  def dragMethod(self, eventObj, trace):
    """Used for changing the value by dragging the line on the canvas. Needs to know the trace it's attached to because they can have different y scales."""
    if self.mode == "constant":
      self.setValue(trace.yToValue(eventObj.y))
    
  def clickMethod(self, eventObj):
    """Used when the line on the canvas is clicked"""
    iface = self.interface
    if iface.mode == 'rename':
      self.setName(iface.nameEntry.get())
      iface.mode = 'select'
    if iface.mode == 'merge':
      if iface.toMerge == None:
	iface.toMerge = self
      elif iface.toMerge != self: #it's easy to click on one line twice, so make sure we're not merging with self
	self.merge(iface.toMerge)
	iface.mode = 'select'
    elif iface.mode == 'select':
      for trace in iface.traces:
	trace.canvas.bind('<B1-Motion>', lambda eventObj: self.dragMethod(eventObj, trace)) #allow the line on the canvas to be dragged after it's clicked on. Need to let it know which trace it's connected to since they have different y scales

class ViewDuration:
  """The class for a duration drawn on the trace"""
  def __init__(self, name, startViewTime, endViewTime, assocViewValue, interface, trace, row=None, locked=False):
    self.name = name
    self.startViewTime = startViewTime
    self.endViewTime = endViewTime
    self.assocViewValue = assocViewValue
    self.interface = interface
    self.trace = trace
    self.row = row
    self.locked = locked #when a duration is locked, it cannot be renamed or dragged, but the value and times it's attached to can still be changed
   
    self.tkLabel = None
    self.tkCheck = None
    self.intVar = Tkinter.IntVar()
    self.intVar.set(0)

  def toDict(self):
    """Retrurns a dict that describes this ViewDuration. For use in saving the experiment."""
    return {'name': self.name, 'start': self.startViewTime.name, 'end': self.endViewTime.name, 'value': self.assocViewValue.name, 'trace': self.trace.name, 'locked': self.locked}
    
  def times(self):
    """Returns an array of the times coverd by this duration: from startTime to endTime in 1ns steps"""
    return range(self.start(), self.end())
    
  def values(self):
    """Returns the values this takes at 1ns times from startTime to endTime"""
    return self.assocViewValue.values(self.times())
      
  def maxValue(self):
    """Returns the maximum value taken during this duration"""
    return max(self.values())

  def minValue(self):
    """Returns the minimum value taken during this duration"""
    return min(self.values())
    
  def setName(self, name):
    """Sets the duration's name and redraws the value frame."""
    if (self.name != name): #if the name isn't a change, don't do anything to avoid redrawing the screen
      if (name not in [d.name for d in self.trace.durations]) and (not self.locked): #make sure no other duration for this trace is using the name 
	self.name = name
	self.redraw()
      else:
	pass #todo: throw error  
  
  def merge(self, toMerge):
    """If toMerge is a duration, this takes its value. If toMerge is a value, this takes it for its value"""
    if isinstance(toMerge, ViewDuration):
      self.assocViewValue = toMerge.assocViewValue
    else: #it's a ViewValue
      self.assocViewValue = toMerge
      
    self.interface.removeUnusedValues() #there could be unused values after the above
    self.interface.refresh()
  
  def setStartViewTime(self, startViewTime):
    """Sets the start time of the duration to the given ViewTime"""
    self.startViewTime = startViewTime
    self.trace.redrawCanvas()
    self.redraw()

  def setEndViewTime(self, endViewTime):
    """Sets the end time of the duration to the given ViewTime"""
    self.endViewTime = endViewTime
    self.trace.redrawCanvas()
    self.redraw()
  
  def setViewValue(self, viewValue):
    """Sets the value associated with the duration to the given ViewValue"""
    self.assocViewValue = viewValue
    self.trace.redrawCanvas()
    self.redraw()
  
  def disp(self, row):
    """Draws a label in the value frame listing the start time name, end time name, and associated value's name"""
    self.row = row
    labelText = self.trace.name + ', ' + self.name + ': ' + self.startViewTime.name + ' ' + self.endViewTime.name + ' ' + self.assocViewValue.name
    
    if self.tkLabel != None:
      self.tkLabel.destroy()
    if self.tkCheck != None:
      self.tkCheck.destroy()

    self.tkLabel = ttk.Label(self.interface.valueFrame, text=labelText)
    self.tkLabel.grid(column=0, row=row, sticky='w', columnspan=2, padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkLabel)

    #the checkbox handles locking the value
    def checkMethod():
      self.locked = (self.intVar.get() == 1)
      
    self.tkCheck = ttk.Checkbutton(self.interface.valueFrame, text='Locked?', command=checkMethod, variable=self.intVar)
    self.tkCheck.grid(column=2, row=row,sticky='w', padx=5, pady=5)   
    self.interface.valueFrameParts.append(self.tkCheck)    
    
  def redraw(self):
    """Redraw the widgets in the value frame in the same row as it was before"""    
    if self.row != None:
      self.disp(self.row)
  
  def split(self, middleViewTime):
    """Returns the two durations that would result from splitting this duration in to two parts at the time given by middleViewTime"""
    return [ViewDuration(self.name + ' part A',self.startViewTime,middleViewTime,self.assocViewValue,self.interface,self.trace, locked=self.locked), ViewDuration(self.name + ' part B',middleViewTime,self.endViewTime,self.assocViewValue,self.interface,self.trace,locked=self.locked)]
  
  def start(self):
    """Returns the time of the start time"""
    return self.startViewTime.time
  
  def end(self):
    """Returns the time of the end time"""
    return self.endViewTime.time
  
  def value(self):
    """Returns the value of the associated value"""
    return self.assocViewValue.value
  
  def dragMethod(self, eventObj):
    """Used for changing the value by dragging the line on the canvas"""
    self.assocViewValue.setValue(self.trace.yToValue(eventObj.y))
    
  def clickMethod(self, eventObj):
    """Used when the line on the canvas is clicked"""
    iface = self.interface
    if iface.mode == 'rename':
      self.setName(iface.nameEntry.get())
      iface.mode = 'select'
    elif iface.mode == 'newValue': #in new value mode, we create a new value for the selected duration using the name in the entry box and copying all other paramters from the current value
      if iface.nameEntry.get() not in [v.name for v in iface.values]:
	newValue = ViewValue(iface.nameEntry.get(), self.assocViewValue.value, self.assocViewValue.locked, iface, functionText=self.assocViewValue.functionText, mode=self.assocViewValue.mode)
	self.assocViewValue = newValue
	iface.values.append(newValue)
	iface.removeUnusedValues() #in case we replaced the last place this value was in use
	iface.redrawValueFrame() #added a new thing to value frame, so need to redraw it from scratch    
	iface.mode = 'select'
    elif iface.mode == 'merge':
      if iface.toMerge == None:
	iface.toMerge = self
      elif iface.toMerge != self: #it's easy to click on one line twice, so make sure we're not merging with self
	self.merge(iface.toMerge)
	iface.mode = 'select'
    elif (iface.mode == 'select') and (self.assocViewValue.mode == 'constant'): #if we're in select mode, and the value can be dragged prepare to move the duration
      if self.assocViewValue in [d.assocViewValue for d in iface.durations() if d != self] != 0:
	#more than one other duration uses this value
	#need to make a new value and come up with a unique name for it; we'll take the name and stick a number on the end. First, find a number that will give a unique name
	count = 1 #count holds the number we'll append to the end of the name
	while self.assocViewValue.name + str(count) in [v.name for v in iface.values]:
	  count += 1
	newValue = ViewValue(self.assocViewValue.name + str(count), self.assocViewValue.value, self.assocViewValue.locked, iface, functionText=self.assocViewValue.functionText, mode=self.assocViewValue.mode)
	iface.values.append(newValue)
	self.assocViewValue = newValue
	iface.redrawValueFrame() #added a new thing to value frame, so need to redraw it from scratch
	
      #the folllwing proc and binding allows the duration's value to be changed. We need to bind to the canvas. Binding to the duration's line alone doesn't cut it; the mouse will move off the line before the refresh and it'll stop working.
      self.trace.canvas.bind('<B1-Motion>', self.dragMethod) #bind the proc to change the value to the canvas
