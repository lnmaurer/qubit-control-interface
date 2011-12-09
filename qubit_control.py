import Tkinter
import ttk
import tkMessageBox
import labrad
import sys


"""
Design overview: The GUI is broken in to two tabs. The setup tab handles LabRAD configuration and
the experiment tab handles the setup of the experiment.

The experiment tab has three frames:
1) The view frame, which has subframes for each trace (a canvas and labels for its axies). Three
things are drawn on each canvas: times, values, and durations. More on these later.
2) The value frame which shows the values associated with the things drawn on the canvas.
3) The control frame, which has buttons that control the effect of clikcing on the canvas (e.g.
allows you to add a new time by clicking on the canvas).

I'll be adding another frame for text based programming.

To handle all this, there are 5 classes. One is for the interface. One is for traces. The other
three are for the times, values, and durations mentioned earlier. A ViewTime keeps track of an x
coordinate; a ViewValue keeps track of a y coordinate; and a ViewDuration keeps track of two
ViewTimes (the start and end of the duration) and a ViewValue (which is the value the trace takes
during the duration). It may not seem like these need their own classes, but they make up the bulk
of the code because there's actually a fair amount to do, like only allowing changes when they're
unlocked, or not allowing a ViewTime's time to cross that of the previous ViewTime.

Each trace shows every time, its own durations, and every value that goes with its own durations.
All times and values are stored in the interface, but each trace has its own set of durations.
Because every trace has every time, and adding times break durations in two, at the moment all
traces have durations with the same start and stop values. I may change that at a later point.
"""

#how on earth does python not have this? Can kind of do it with filter or Comprehensions, but ugly
#since you want an item but get a list which you have to remove the item from
def find(f, seq):
  """Return first item in sequence where f(item) == True. Returns None if there aren't any such items."""
  for item in seq:
    if f(item): 
      return item

class ViewTime:
  """The class for a time drawn on the trace"""
  def __init__(self, name, value, locked, interface, row=None):
    self.name = name
    self.value = value
    self.locked = locked
    self.interface = interface
    self.row = row
    
    self.stringVar = Tkinter.StringVar()
    self.stringVar.set(str(value))
    self.intVar = Tkinter.IntVar()
    self.intVar.set(1 if self.locked else 0)
    self.tkLabel = None
    self.tkEntry = None
    self.tkCheck = None
  
  def setValue(self, value, errorIfImpossible=False):
    """
    The value of a ViewTime is a time. It can only be set if it isn't locked.
    
    If errorIfImpossible is set to True, the method will throw an error if it can't be set to the requested value.
    """
    if (self.value != value) and (not self.locked):
      sortedTimes =  [t.value for t in self.interface.times]
      sortedTimes.sort()
      index = sortedTimes.index(self.value)
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
	
      if ((maxTime == None) and (value > minTime)) \
	or ((maxTime != None) and (minTime != None) and (value > minTime) and (value < maxTime)):
	self.value = value
	#since times are on every trace, need to update all of them
	self.interface.redrawAllCanvases()
	self.interface.redrawAllXaxies()
      elif errorIfImpossible: #can't be set to the requested time
	pass #todo: throw an error
    elif (self.value != value) and errorIfImpossible: #can't be set to the requested time because it's locked
	pass #todo: throw an error
	
    #by keeping this outside the previous if statement, the tkEntry is restored to the old value if an unacceptable value was entered
    self.stringVar.set(str(self.value))
  
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

    #this method updates the value if it's changed in the entry box
    def entryMethod(eventObj):
      if self.tkEntry.get() != '':
	self.setValue(float(self.tkEntry.get()))
      return 1
    self.tkEntry.bind("<Return>",entryMethod)
    
    #the checkbox handles locking the value
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
    """Used for changing the value by dragging the line on the canvas"""
    self.setValue(self.interface.xToTime(eventObj.x))
    
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
  def __init__(self,name, value, locked, interface, row=None):
    self.name = name
    self.value = value
    self.locked = locked
    self.interface = interface
    self.row = row
    
    self.stringVar = Tkinter.StringVar()
    self.stringVar.set(str(value))
    self.intVar = Tkinter.IntVar()
    self.intVar.set(1 if self.locked else 0)
    self.tkLabel = None
    self.tkEntry = None
    self.tkCheck = None
  
  def setValue(self, value, errorIfImpossible=False):
    """
    The value of a ViewValue is a voltage. It can only be set if it isn't locked
        
    If errorIfImpossible is set to True, the method will throw an error if it can't be set to the requested value.
    """
    if (self.value != value) and (not self.locked):
      if value >= 0: #don't allow negative values
	self.value = value
      
	#update all the traces which have this value
	for trace in [t for t in self.interface.traces if self in t.values()]:
	  trace.redrawCanvas()
	  trace.redrawYaxis()
      else:
	pass #todo: value < 0 so raise error
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
	self.setValue(float(self.tkEntry.get()))
      return 1
    self.tkEntry.bind("<Return>",entryMethod)
    
    #the checkbox handles locking the value
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
  
  def dragMethod(self, eventObj, trace):
    """Used for changing the value by dragging the line on the canvas. Needs to know the trace it's attached to because they can have different y scales."""
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
    return self.startViewTime.value
  
  def end(self):
    """Returns the time of the end time"""
    return self.endViewTime.value
  
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
    elif iface.mode == 'merge':
      if iface.toMerge == None:
	iface.toMerge = self
      elif iface.toMerge != self: #it's easy to click on one line twice, so make sure we're not merging with self
	self.merge(iface.toMerge)
	iface.mode = 'select'
    elif iface.mode == 'select': #if we're in select mode, then prepare to move the duration
      if self.assocViewValue in [d.assocViewValue for d in iface.durations() if d != self] != 0:
	#more than one other duration uses this value
	#need to make a new value and come up with a unique name for it; we'll take the name and stick a number on the end. First, find a number that will give a unique name
	count = 1 #count holds the number we'll append to the end of the name
	while self.assocViewValue.name + str(count) in [v.name for v in iface.values]:
	  count += 1
	newValue = ViewValue(self.assocViewValue.name + str(count), self.assocViewValue.value, self.assocViewValue.locked,iface)
	iface.values.append(newValue)
	self.assocViewValue = newValue
	iface.redrawValueFrame() #added a new thing to value frame, so need to redraw it from scratch
	
	#the folllwing proc and binding allows the duration's value to be changed. We need to bind to the canvas. Binding to the duration's line alone doesn't cut it; the mouse will move off the line before the refresh and it'll stop working.
	self.trace.canvas.bind('<B1-Motion>', self.dragMethod) #bind the proc to change the value to the canvas

class ViewTrace:
  """Handles all the widgets for one trace and the durations that go with it"""
  def __init__(self, name, interface, row, initialValue):
    self.name = name
    self.interface = interface
    self.row = row
    self.times = interface.times
    
    self.viewFrame = ttk.Labelframe(self.interface.viewFrame, text=name)
    self.viewFrame.grid (column=0, row=self.row, sticky='nsew', padx=5, pady=5)
    
    self.xAxisLables = [] #will store all the widgets for the x-axis
    self.yAxisLables = [] #will store all the widgets for the y-axis
    #the next three are used to store the current axis start/stop so that we can tell if they've changed
    self.startValue = None
    self.endValue = None
    self.maxY = None

    #to save typing '.interface' a bazillion times:
    self.timeToX = self.interface.timeToX
    self.xToTime = self.interface.xToTime
    self.viewWidth = self.interface.viewWidth
    self.viewHeight = self.interface.viewHeight
    self.start = self.interface.start
    self.end = self.interface.end    
    
    #creat a duration with the initial value
    self.durations = [ViewDuration('Initial', self.start, self.end, initialValue, self.interface, self)]
    
    self.canvas = Tkinter.Canvas(self.viewFrame, width=self.interface.viewWidth, height=self.interface.viewHeight) #todo: make array so that we can have more than one view
    self.canvas.grid(column=1, row=0, columnspan=3, rowspan=3, sticky='nsew', padx=5, pady=5)
  
    self.canvas.bind("<Button-1>",  self.canvasClick)  
    
    #make it so that, after dragging an element has ceased, the binding is reset so that further dragging won't move the element unless it gets clicked again first
    #we do this by binding to any motion on any canvas
    self.canvas.bind("<Motion>", self.interface.clearCanvasBindings)
    
    self.redrawCanvas()
    self.redrawXaxis()
    self.redrawYaxis() 

  def redrawCanvas(self):
    """Clears the canvas and redraws everything on it"""
    
    #first, clear everything off the canvas (but don't delete the canvas itself)
    self.canvas.delete('all')
    
    #next, draw all the ViewTimes
    for time in self.interface.times:
      if (time.name != 'start') and (time.name != 'end'): #don't display anything for start or stop times; that way they can't be edited through the canvas
	lineID = self.canvas.create_line(self.timeToX(time.value), 0, self.timeToX(time.value), self.viewHeight, width=2, dash='.') #draw the line
	self.canvas.tag_bind(lineID, "<Button-1>",  time.clickMethod) #bind the line to it's clickMethod so that it can be interacted with

    #next, draw all the ViewValues
    for value in self.values():
      lineID = self.canvas.create_line(0, self.valueToY(value.value), self.viewWidth, self.valueToY(value.value), width=1, fill='red', dash='.')
      self.canvas.tag_bind(lineID, "<Button-1>",  value.clickMethod)

    #finially, draw all the ViewDurations. Because this comes last, it's drawn over the ViewValues. That means that when you click a duration, you don't get the ViewValue underneath.
    for dur in self.durations:
      lineID = self.canvas.create_line(self.timeToX(dur.start()), self.valueToY(dur.value()), self.timeToX(dur.end()), self.valueToY(dur.value()), width=2, fill='red')
      self.canvas.tag_bind(lineID, "<Button-1>",  dur.clickMethod)
  
  def redrawXaxis(self):
    """Redraws the x-axis lables"""
    
    #only redraw if something has changed
    if (self.startValue != self.start.value) or (self.endValue != self.end.value):
      for l in self.xAxisLables:
	l.destroy()
      
      self.xAxisLables = []
    
      self.startValue = self.start.value
      tmp = ttk.Label(self.viewFrame, text=str(self.startValue))
      tmp.grid(column=1, row=3, sticky='w', padx=0, pady=5)
      self.xAxisLables.append(tmp)
    
      tmp = ttk.Label(self.viewFrame, text='Time (UNITS???)')
      tmp.grid(column=2, row=3, sticky='ew', padx=0, pady=5)
      self.xAxisLables.append(tmp)
    
      self.endValue = self.end.value
      tmp = ttk.Label(self.viewFrame, text=str(self.endValue))
      tmp.grid(column=3, row=3, sticky='e', padx=0, pady=5)
      self.xAxisLables.append(tmp)
  
  def redrawYaxis(self):
    """Redraws the y-axis lables"""
    
    #only redraw if the max value has changed; the bottom of the plot is always at zero
    if self.maxY != self.maxValue():
      for l in self.yAxisLables:
	l.destroy()
	
      self.yAxisLables = []
      
      self.maxY = self.maxValue()
      tmp = ttk.Label(self.viewFrame, text=str(self.maxY))
      tmp.grid(column=0, row=0, sticky='ne', padx=0, pady=5)
      self.yAxisLables.append(tmp)
    
      tmp = ttk.Label(self.viewFrame, text='??? (UNITS???)')
      tmp.grid(column=0, row=1,sticky='nse', padx=0, pady=5)
      self.yAxisLables.append(tmp)
    
      tmp = ttk.Label(self.viewFrame, text = '0')
      tmp.grid(column=0, row=2,sticky='se', padx=0, pady=5)
      self.yAxisLables.append(tmp)
  
  def values(self):
    """Returns a list of all values associated with durations drawn on this trace"""
    return [d.assocViewValue for d in self.durations]

  def canvasClick(self, eventObj):
    """This is called when the canvas is clicked"""
    if (self.interface.mode == 'addTime'):
      self.interface.addTime(eventObject=eventObj)

  def addTime(self, newTime):
    """Adds a new time to the canvas and adjust the durations to fit."""
    toSplit = find(lambda d: (d.start() < newTime.value) and (d.end() > newTime.value), self.durations)
    self.durations.remove(toSplit) #remove the duration that's getting chopped by this
    self.durations.extend(toSplit.split(newTime)) #add the two new durations
    self.redrawCanvas() #we've added a new time, so have to redraw canvas
     
  def deleteTime(self, viewTime):
    #plan: find the two durations that border this time, and delete one. Set the end time of the remaining one to the end time of the deleted one
    #todo: GIVE OPTION FOR WHICH OF THE TWO DURATIONS TO CHOOSE THE VALUE FROM???
    firstDuration = self.durationEndingAt(viewTime)
    secondDuration = self.durationStartingAt(viewTime)
    firstDuration.endViewTime = secondDuration.endViewTime #change first duration so that it covers bother durations
    self.durations.remove(secondDuration) #get rid of second duration
     
  def maxValue(self):
    """Returns 1.25 times the value of the largest ViewValue so that the trace can be scaled directly on the canvas"""
    rawvalues =  [d.assocViewValue.value for d in self.durations]
    rawvalues.sort()
    maxValue = rawvalues[-1]
    if maxValue == 0:
      return 1.0 #returning zero would result in divide by zero errors later
    else:
      return 1.25*maxValue #return 1.25 times the largest value
  
  def valueToY(self, value):
    """Converts from value to canvas y coordinate"""
    return -float(self.interface.viewHeight)/self.maxValue() * value + self.interface.viewHeight
    
  def yToValue(self, y):
    """Converts from canvas y coordinate to value"""
    return -self.maxValue()/self.interface.viewHeight * y + self.maxValue() 
    
  def sortedDurations(self):
    """Returns the durations, sorted from first to last"""
    return sorted(self.durations, lambda d: d.startViewTime.value)
    
  def durationStartingAt(self, viewTime):
    """Returns the duration starting at the given ViewTime"""
    return find(lambda d: d.startViewTime == viewTime, self.durations)
    
  def durationEndingAt(self, viewTime):
    """Returns the duration ending at the given time"""
    return find(lambda d: d.endViewTime == viewTime, self.durations)
    
  def durationNamed(self, name):
    """Returns the duration named name"""  
    return find(lambda d: d.name == name, self.durations)
    
class Interface:
  """The class for the GUI interface"""
  
  viewWidth = 500 #width of the view canvas
  viewHeight = 100 #height of the view canvas

  def __init__(self):
#The LabRAD connection
    self.labRADconnection = None #don't connect until later
    
#The root. This has to come before the other GUI stuff, because 'StringVar's and 'IntVar's in the 'View____'s need it to be initialized before they can be created.
    self.root = Tkinter.Tk()
    self.root.title('Qubit Control')
    
#The menubar and menus
    menubar = Tkinter.Menu(self.root)
    
    #the file menu
    self.filemenu = Tkinter.Menu(menubar, tearoff=0)
    self.filemenu.add_command(label="Save Experiment", state='disabled', command=self.saveExperiment)
    self.filemenu.add_command(label="Load Experiment", state='disabled', command=self.loadExperiment)
    self.filemenu.add_separator()
    self.filemenu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit) #todo: make key binding work
    self.root.bind_all('<Control-q>', lambda arg: self.root.quit()) #control-q now quits
    menubar.add_cascade(label="File", menu=self.filemenu)
    
    #the edit menu
    editmenu = Tkinter.Menu(menubar, tearoff=0)
    editmenu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.noteBook.event_generate('<Control-x>')) #todo: make it work
    editmenu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.noteBook.event_generate('<Control-c>')) #todo: make it work
    editmenu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.noteBook.event_generate('<Control-v>')) #todo: make it work
    menubar.add_cascade(label="Edit", menu=editmenu)
    
    self.root.config(menu=menubar)
#the notebook has two pages, one for setup and one for the experiment
    self.noteBook = ttk.Notebook(self.root)
    self.noteBook.pack()
    self.setupTab = ttk.Frame(self.noteBook)
    self.experimentTab = ttk.Frame(self.noteBook)
    self.setupTab.pack()
    self.experimentTab.pack()
    #names for the tabs
    self.noteBook.add(self.setupTab, text='Setup')
    self.noteBook.add(self.experimentTab, text='Experiment', state='disabled') #experiment tab starts out disabled; it's enabled after we connect to a server and set up traces
    
#set some variables used by the GUI
    self.mode = 'select' #mode determines what clikcing on the canvas will do. Options are 'select', 'addTime', 'deleteTime', 'merge', and 'rename'

#The setup tab
    #the manager address entry
    ttk.Label(self.setupTab, text='Manager address:').grid(column=0, row=0, sticky='e', padx=5, pady=5)
    self.managerAddress = Tkinter.StringVar()
    self.managerAddress.set('localhost') #todo: read out of a config file that saves previous entry
    ttk.Entry(self.setupTab, textvariable=self.managerAddress).grid(column=1, row=0, sticky='w', padx=5, pady=5)   

    #the manager port entry
    ttk.Label(self.setupTab, text='Manager port:').grid(column=0, row=1, sticky='e', padx=5, pady=5)
    self.managerPort = Tkinter.StringVar()
    self.managerPort.set('7682') #todo: read out of a config file that saves previous entry
    ttk.Entry(self.setupTab, textvariable=self.managerPort).grid(column=1, row=1, sticky='w', padx=5, pady=5)
    
    #the manager password
    ttk.Label(self.setupTab, text='Manager password:').grid(column=0, row=2, sticky='e', padx=5, pady=5)
    self.managerPassword = Tkinter.StringVar()
    self.managerPassword.set('test') #todo: read out of a config file that saves previous entry
    ttk.Entry(self.setupTab, textvariable=self.managerPassword, show='*').grid(column=1, row=2, sticky='w', padx=5, pady=5)
    
    #button to connect to manager
    def connectToManager():
      #todo: error handling for when the following doesn't work
      self.labRADconnection = labrad.connect(self.managerAddress.get(),
					     port=int(self.managerPort.get()),
					     password=self.managerPassword.get())
      self.serverListbox.delete(0, Tkinter.END) #if the listbox is already populated, clear it, this is unnescessary at present
      for serverName in str(self.labRADconnection.servers).rsplit("\n"):
	self.serverListbox.insert(Tkinter.END, serverName) #add all the server names to the listbox
	
      
    ttk.Button(self.setupTab, text='Connect', command=connectToManager).grid(column=1, row=3,sticky='nsew', padx=5, pady=5)

    #the listbox that will show the available servers
    ttk.Label(self.setupTab, text='Available Servers:').grid(column=2, row=0, sticky='s', padx=30, pady=5)
    self.serverListbox = Tkinter.Listbox(self.setupTab, height=8, selectmode=Tkinter.MULTIPLE) #todo: is there now ttk version of this?
    self.serverListbox.grid(column=2, row=1, rowspan=8, sticky='n', padx=0, pady=5)
    scrollbar = ttk.Scrollbar(self.setupTab, orient=Tkinter.VERTICAL, command=self.serverListbox.yview)
    scrollbar.grid(column=3, row=1, rowspan=8, sticky='nsw', padx=0, pady=5)
    self.serverListbox.configure(yscrollcommand=scrollbar.set)
    
    #once the servers are selected in the listbox, clicking this button will make traces for the selected servers
    def makeTraces():
      makeTracesButton.config(state='disabled') #for now, we disable the button after it's clicked, this means traces can be made only once
      self.noteBook.tab(1, state='normal') #the experiment tab is in position 1, so that's what we enable
      self.populateExperimentTab() #now that we know how many traces to make, we can draw the experiment tab
      
    makeTracesButton = ttk.Button(self.setupTab, text='make traces for selected', command=makeTraces)
    makeTracesButton.grid(column=2, row=9, sticky='n', padx=5, pady=5)

  def populateExperimentTab(self):
    """Populates the experiment tab with widgets; call after deciding what servers we want traces for"""

#enable experiment loading and saving
    self.filemenu.entryconfigure('Save Experiment', state="normal")    
    self.filemenu.entryconfigure('Load Experiment', state="normal")    
    
#initial conditions for the traces
    self.start = ViewTime('start',0.0,True,self)
    self.end = ViewTime('end',1000.0,True,self)
    initialValue = ViewValue('Initial',1,False,self)
    self.times = [self.start, self.end]
    self.values = [initialValue]
    
#The control frame
    self.controlFrame = ttk.Labelframe(self.experimentTab, text='Controls')
    self.controlFrame.grid(column=0,row=1,sticky='nsew',padx=5,pady=5)
   
    def addTimeMode():
      self.mode = 'addTime'
      self.nameEntry.focus_set() #move focus to nameEntry box when clicked
    ttk.Button(self.controlFrame, text='Add Time', command=addTimeMode).grid(column=0, row=0,sticky='w', padx=5, pady=5)
 
    def deleteTimeMode():
      self.mode = 'deleteTime'
    ttk.Button(self.controlFrame, text='Delete Time', command=deleteTimeMode).grid(column=1, row=0, sticky='w', padx=5, pady=5)

    def mergeMode():
      self.mode = 'merge'
      self.toMerge = None #need two things to merge; this holds the first one
    ttk.Button(self.controlFrame, text='Merge', command=mergeMode).grid(column=2, row=0, sticky='w', padx=5, pady=5)    
    
    def renameMode():
      self.mode = 'rename'
      self.nameEntry.focus_set() #move focus to nameEntry box when clicked
    ttk.Button(self.controlFrame, text='Rename', command=renameMode).grid(column=3, row=0, sticky='w', padx=5, pady=5)

    ttk.Label(self.controlFrame, text="Name:").grid(column=4, row=0, sticky='e', padx=5, pady=5)
    
    self.nameEntry = ttk.Entry(self.controlFrame)
    self.nameEntry.grid(column=5, row=0,sticky='w', padx=5, pady=5)

#The view frame and canvas
    #print [int(i) for i in self.serverListbox.curselection()]
    self.viewFrame = ttk.Labelframe(self.experimentTab,text='Traces')
    self.viewFrame.grid(column=0,row=0,sticky='nsew',padx=5,pady=5)

    self.traces = []
    
    #todo: populate self.traces correctly
    self.traces.append(ViewTrace('test', self, 0, initialValue))
    self.traces.append(ViewTrace('test2', self, 1, initialValue))
    
#The value frame
    self.valueFrameParts = []

    self.valueFrame = ttk.Labelframe(self.experimentTab,text='Values')
    self.valueFrame.grid(column=1, row=0, sticky='nsew', rowspan=3, padx=5, pady=5)
    self.valueFrameParts = [] #will contain all the widgets in the value frame so that we can destroy them even after the object they belong to gets destroyed
    self.redrawValueFrame()
  
#The code frame
    self.codeFrame = ttk.Labelframe(self.experimentTab,text='Code')
    self.codeFrame.grid(column=0, row=2, sticky='nsew', padx=5, pady=5)
    
    self.codeText = Tkinter.Text(self.codeFrame, width=80, height=10, wrap='none')
    self.codeText.grid(column=0, row=0, columnspan=3, sticky='se')
    yscrollbar = ttk.Scrollbar(self.codeFrame, orient=Tkinter.VERTICAL, command=self.codeText.yview)
    yscrollbar.grid(column=3, row=0, sticky='nsw')
    self.codeText.configure(yscrollcommand=yscrollbar.set)
    xscrollbar = ttk.Scrollbar(self.codeFrame, orient=Tkinter.HORIZONTAL, command=self.codeText.xview)
    xscrollbar.grid(column=0, row=1, columnspan=3, sticky='new')
    self.codeText.configure(xscrollcommand=xscrollbar.set)
    
    ttk.Button(self.codeFrame, text='Test Code').grid(column=0, row=2, padx=5, pady=5)
    
    def runCode():
      try:
	exec self.codeText.get('1.0', 'end') in globals()
      except:
	#todo: better message
	tkMessageBox.showerror("Error", "{!s}\n{!s}\n{!s}".format(*sys.exc_info()))
      
    ttk.Button(self.codeFrame, text='Run Code', command=runCode).grid(column=1, row=2, padx=5, pady=5)
    ttk.Button(self.codeFrame, text='Load Code').grid(column=2, row=2, padx=5, pady=5)
    
  def redrawValueFrame(self):
    """Completely redraws the value frame of the interface"""
    
    #first, clear out all the old stuff from the frame
    for l in self.valueFrameParts:
      l.destroy()
    
    self.valueFrameParts = [] #array to store the parts so that we can destroy them when redrawing the frame

    #first, we display all the ViewTimes. A heading label comes first.
    tmp = ttk.Label(self.valueFrame, text="Times")
    tmp.grid(column=0, row=0, columnspan=2, padx=5, pady=5)
    self.valueFrameParts.append(tmp)
    
    row = 1 #keeps track of what row we're on The heading was on row 0
    
    for el in self.times:
      el.disp(row)
      row += 1

    #next, we display all the ViewValues. A heading label comes first.      
    tmp = ttk.Label(self.valueFrame, text="Values")
    tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
    self.valueFrameParts.append(tmp)
    
    row +=1
    
    for el in self.values:
      el.disp(row)
      row += 1

    #finially, we display all the ViewDurations. A heading label comes first.
    tmp = ttk.Label(self.valueFrame, text="Durations")
    tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
    self.valueFrameParts.append(tmp)    
    
    row +=1
    
    for el in self.durations():
      el.disp(row)
      row += 1
  
  def refresh(self):
    """Redraw all the parts of the GUI that can change"""
    self.redrawAllCanvases()
    self.redrawAllXaxies()
    self.redrawAllYaxies()
    self.redrawValueFrame()
    
  def clearCanvasBindings(self, eventObj):
    """Clears the <B1-Motion> binding for all canvases"""
    for canvas in [t.canvas for t in self.traces]:
      canvas.bind("<B1-Motion>", lambda e: None)
    
  def redrawAllCanvases(self):
    """Redraws all the canvases"""
    for trace in self.traces:
      trace.redrawCanvas()
      
  def redrawAllXaxies(self):
    """Redraws all the x axies"""
    for trace in self.traces:
      trace.redrawXaxis() 

  def redrawAllYaxies(self):
    """Redraws all the y axies"""
    for trace in self.traces:
      trace.redrawYaxis() 

  def durations(self):
    """Returns a list of all the durations in all the traces"""
    durations = []
    for trace in self.traces:
      durations.extend(trace.durations)
    return durations
    
  def canvases(self):
    """Returns a list of all canvases"""
    return [t.canvas for t in self.traces]
    
  def bindCanvasesDrag(self, method):
    """Binds all canvases' <B1-Motion> (left mouse drag) to the given method."""
    for canvas in self.canvases():
      canvas.bind('<B1-Motion>', method)
    
  #all traces have the same x axis, so we can keep these functions in the interface
  def maxTime(self):
    """Returns the time of the largest ViewTime"""
    return self.end.value
  
  def timeToX(self, time):
    """Coverts from time to canvas x coordinate"""
    return float(self.viewWidth)/self.maxTime() * time
  
  def xToTime(self, x):
    """Converts from canvas x coordinate to time"""
    return float(self.maxTime())/self.viewWidth * x
  
  def setValue(self, nameString, newValue):
    """Sets the value with name nameString to newValue"""
    self.valueNamed(nameString).setValue(newValue, True)
      
  def setTime(self, nameString, newTime):
    """Sets the time with name nameString to newTime"""
    self.timeNamed(nameString).setValue(newTime, True)
      
  def addTime(self, name=None, time=None, eventObject=None):
    """Adds a time, either given by a name and time, or by a click on the canvas and the name in the entry box. Then it updates the traces."""
    if eventObject != None: #then this addTime was in response to a click
      name = self.nameEntry.get()
      time = self.xToTime(eventObject.x)
      self.mode = 'select' #go back to select mode
    
    #todo: throw error if before start of after end
    if time <= self.start.value:
      pass
    if time >= self.end.value:
      pass
    
    if name not in [t.name for t in self.times]: #there aren't any other times with this name
      newTime = ViewTime(name,time,False,self)
      self.times.append(newTime) #add this new time to the list of times
      
      for trace in self.traces:
	trace.addTime(newTime)
      
      self.redrawValueFrame() #added a new time (and thus new durations), so redraw the value frame
    else: #there's already a time with that name
      pass #todo: throw an error
      
  def deleteTime(self, name=None, viewTime=None):
    """Deletes the time given or named. Then it updates the traces."""
    if viewTime == None: #lookup time by name
      viewTime = find(lambda vt: vt.name==name, self.times)
      
    #todo: throw error if trying to delete start, end, or a locked time
    if viewTime == self.start:
      pass
    elif viewTime == self.end:
      pass
    elif viewTime.locked:
      pass
    
    for trace in self.traces: #there's a duration to remove in every trace
      trace.deleteTime(viewTime)

    #it could be that there are values no longer in use now that we deleted some durations. If so, remove them.
    self.removeUnusedValues()

    self.times.remove(viewTime) #get rid of the time	      
    self.refresh() #need to refresh since we've updated the value frame, and the canvas may need updating if the unless statement ran
  
  def removeUnusedValues(self):
    """Removes all the values that aren't used in at least one duration."""
    valuesInUse = [d.assocViewValue for d in self.durations()]
    self.values = filter(lambda v: v in valuesInUse, self.values) #values now only has values in use
  
  def timeNamed(self, name):
    """Returns the time with the given name"""
    time = find(lambda t: t.name == name, self.times)
    if time == None:
      raise NameError("There is no time named {}.".format(name))
    else:
      return time
    
  def valueNamed(self, name):
    """Returns the value with the given name"""
    value = find(lambda v: v.name == name, self.values)
    if time == None:
      raise NameError("There is no value named {}.".format(name))
    else:
      return value
    
  def traceNamed(self, name):
    """Returns the trace with the given name"""
    trace = find(lambda t: t.name == name, self.traces)
    if trace == None:
      raise NameError("There is no teace named {}.".format(name))
    else:
      return trace
      
  def loadExperiment(self):
    pass
  
  def saveExperiment(self):
    pass
      
      
if __name__ == "__main__":
  gui = Interface() #make the interface

  #the following functions will come in useful when evaluating code in code frame
  def setValue(nameString, newValue):
    gui.setValue(nameString, newValue)
    
  def setTime(nameString, newTime):
    gui.setTime(nameString, newTime)
    
  def addTime(name, time):
    gui.addTime(name=name, time=time)
    
  def deleteTime(name):
    gui.deleteTime(name=name)
    
  def setDurationValue(traceName, durationName, valueName):
    trace = gui.traceNamed(traceName)
    duration = trace.durationNamed(durationName)
    value = gui.valueNamed(valueName)
    duration.setViewValue(value)
    
  def mergeValues(valueNameA, valueNameB):
    valueA = gui.valueNamed(valueNameA)
    valueB = gui.valueNamed(valueNameB)
    valueB.merge(valueA)
    
  def setDurationName(traceName, startTimeName, newDurationName):
    trace = gui.traceNamed(traceName)
    time = gui.timeNamed(startTimeName)
    trace.durationStartingAt(time).setName(newDurationName)
    
  gui.root.mainloop() #set everything in motion