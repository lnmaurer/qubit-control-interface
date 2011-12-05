import Tkinter
import ttk


"""
Design overview: The GUI is broken in to two tabs. The setup tab handles LabRAD configuration and
the experiment tab handles the setup of the experiment.

The experiment tab has three frames:
1) The view frame, which has the canvas where the trace is drawn (will later have multiple canvases
for multiple traces). Three things are drawn on the canvas: times, values, and durations. More on
these later.
2) The value frame which shows the values associated with the things drawn on the canvas.
3) The control frame, which has buttons that control the effect of clikcing on the canvas (e.g.
allows you to add a new time by clicking on the canvas).

I'll be adding another frame for text based programming.

To handle all this, there are 4 classes. One is for the interface. The other three are for the
times, values, and durations mentioned earlier. A ViewTime keeps track of an x coordinate; a
ViewValue keeps track of a y coordinate; and a ViewDuration keeps track of two ViewTimes (the start
and end of the duration) and a ViewValue (which is the value the trace takes during the duration).
It may not seem like these need their own classes, but they make up the bulk of the code because
there's actually a fair amount to do, like only allowing changes when they're unlocked, or not
allowing a ViewTime's time to cross that of the previous ViewTime.
"""

class ViewTime:
  """The class for a time drawn on the graph"""
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
  
  def setValue(self, value):
    """The value of a ViewTime is a time. It can only be set if it isn't locked."""
    if (self.value != value) and (not self.locked):
      sortedTimes =  [t.value for t in self.interface.times]
      sortedTimes.sort()
      index = sortedTimes.index(self.value)
      #find the limits for what this time can be set to
      if index == 0: #in this case, self is the smallest time
	minTime = None
	maxTime = sortedTimes[index+1]
      elif index == (len(sortedTimes)-1): #in this case, self is the largest time
	minTime = sortedTimes[index-1]
	maxTime = None
      else:
	minTime = sortedTimes[index-1]
	maxTime = sortedTimes[index+1]
	
      if ((maxTime == None) and (value > minTime)) \
	or ((minTime == None) and (value < maxTime)) \
	or ((maxTime != None) and (minTime != None) and (value > minTime) and (value < maxTime)):
	self.value = value
	self.interface.redrawCanvas()
	self.interface.redrawAxisLabels()

    #by keeping this outside the previous if statement, the tkEntry is restored to the old value if an unacceptable value was entered
    self.stringVar.set(str(self.value))
  
  def setName(self, name):
    """Sets the time's name and redraws the value frame. The name can only be changed if the time isn't locked."""
    if (self.name != name) and (not self.locked): #The first condition prevents needless refreshes if the name hasn't changed
      self.name = name
      self.interface.redrawValueFrame() #the description of any associated durations will have to be redrawn to reflect this time's new name
  
  def disp(self, row):
    """Draws the widgets associated with this time in the value frame: a label with the name, an entry box with the value, and a checkbox for locking it."""
    self.row = row

    #get rid of old widgets if they exsist
    if self.tkLabel != None:
      self.tkLabel.destroy()
    if self.tkEntry != None:
      self.tkEntry.destroy()
    
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
	self.interface.redrawCanvas()
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
    if (iface.mode == 'rename') and (iface.nameEntry.get() not in [t.name for t in iface.times]):
      self.setName(iface.nameEntry.get()) #set the name if we're in rename mode
      iface.mode = 'select'
    elif iface.mode == 'select':
      iface.view.bind('<B1-Motion>', self.dragMethod) #allow the line on the canvas to be dragged after it's clicked on
    elif (iface.mode == 'deleteTime') and not self.locked:
      #plan: find the two durations that border this time, and delete one. Set the end time of the remaining one to the end time of the deleted one
      #todo: GIVE OPTION FOR WHICH OF THE TWO DURATIONS TO CHOOSE THE VALUE FROM???
      firstDuration = [d for d in iface.durations if d.endViewTime == self].pop()
      secondDuration = [d for d in iface.durations if d.startViewTime == self].pop()
      firstDuration.endViewTime = secondDuration.endViewTime
      iface.durations.remove(secondDuration) #get rid of second duration
      iface.times.remove(self) #get rid of self
    
      #delete the associated value if there isn't another duration using that value
      if secondDuration.assocViewValue not in [d.assocViewValue for d in iface.durations]:
	iface.values.remove(secondDuration.assocViewValue)
	      
      iface.refresh() #need to refresh since we've updated the value frame, and the canvas may need updating if the unless statement ran
      iface.mode = 'select'
  
class ViewValue:
  """The class for a value drawn on the graph"""
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
  
  def setValue(self, value):
    """The value of a ViewValue is a voltage. It can only be set if it isn't locked"""
    if (self.value != value) and (not self.locked):
      self.value = value
      self.stringVar.set(str(value))
      
      self.interface.redrawCanvas()
      self.interface.redrawAxisLabels()
  
  def setName(self, name):
    """Sets the value's name and redraws the value frame. The name can only be changed if the value isn't locked."""
    if (self.name != name) and (not self.locked): #The first condition prevents needless refreshes if the name hasn't changed
      self.name = name
      self.interface.redrawValueFrame() #the description of any associated durations will have to be redrawn to reflect this value's new name
  
  def disp(self, row):
    """Draws the widgets associated with this value in the value frame: a label with the name, an entry box with the value, and a checkbox for locking it."""
    self.row = row

    #get rid of old widgets if they exsist
    if self.tkLabel != None:
      self.tkLabel.destroy()
    if self.tkEntry != None:
      self.tkEntry.destroy()
    
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
	self.interface.redrawCanvas()
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
    self.setValue(self.interface.yToValue(eventObj.y))
    
  def clickMethod(self, eventObj):
    """Used when the line on the canvas is clicked"""
    iface = self.interface
    if iface.mode == 'rename':
      #if this ViewValue is renamed to a name already in use, we merge this ViewValue with the ViewValue sharing its new name
      newName = iface.nameEntry.get() #the new name
      valuesWithSameName = [v for v in iface.values if v.name == newName] #look for another value with this name
      if len(valuesWithSameName) != 0:
	#if the named value does exist, we'll get rid of the current value and replace it everywhere with the named value	    
	iface.values.remove(self) #get rid of the current value from the list
	replacementValue = valuesWithSameName.pop()
	  
	for dur in [d for d in iface.durations if d.assocViewValue == self]:
	  dur.assocViewValue = replacementValue
      else: #no value uses that name
	self.setName(newName) #if no value with this name already exists, merely change the name of self
      iface.refresh() #number of values can change, and the duration section of the viewframe needs to be redrawn since this value's name has changed      
      iface.mode = 'select'
    elif iface.mode == 'select':
      iface.view.bind('<B1-Motion>', self.dragMethod) #allow the line on the canvas to be dragged after it's clicked on

class ViewDuration:
  """The class for a duration drawn on the graph"""
  def __init__(self, name, startViewTime, endViewTime, assocViewValue, interface, row=None):
    self.name = name
    self.startViewTime = startViewTime
    self.endViewTime = endViewTime
    self.assocViewValue = assocViewValue
    self.interface = interface
    self.row = row
   
    self.tkLabel = None
  
  def setName(self, name):
    """Sets the duration's name and redraws the value frame."""
    if self.name != name:
      self.name = name
      self.redraw()  
  
  def setStartViewTime(self, startViewTime):
    """Sets the start time of the duration to the given ViewTime"""
    self.startViewTime = startViewTime
    self.interface.redrawCanvas()
    self.redraw()

  def setEndViewTime(self, endViewTime):
    """Sets the end time of the duration to the given ViewTime"""
    self.endViewTime = endViewTime
    self.interface.redrawCanvas()
    self.redraw()
  
  def setViewValue(self, viewValue):
    """Sets the value associated with the duration to the given ViewValue"""
    self.assocViewValue = viewValue
    self.interface.redrawCanvas()
    self.redraw()
  
  def disp(self, row):
    """Draws a label in the value frame listing the start time name, end time name, and associated value's name"""
    self.row = row
    labelText = self.name + ': ' + self.startViewTime.name + ' ' + self.endViewTime.name + ' ' + self.assocViewValue.name
    
    if self.tkLabel != None:
      self.tkLabel.destroy()

    self.tkLabel = ttk.Label(self.interface.valueFrame, text=labelText)
    self.tkLabel.grid(column=0, row=row, sticky='w', columnspan=3, padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkLabel)
  
  def redraw(self):
    """Redraw the widgets in the value frame in the same row as it was before"""    
    if self.row != None:
      self.disp(self.row)
  
  def split(self, middleViewTime):
    """Returns the two durations that would result from splitting this duration in to two parts at the time given by middleViewTime"""
    return [ViewDuration(self.name + ' part A',self.startViewTime,middleViewTime,self.assocViewValue,self.interface), ViewDuration(self.name + ' part B',middleViewTime,self.endViewTime,self.assocViewValue,self.interface)]
  
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
    self.assocViewValue.setValue(self.interface.yToValue(eventObj.y))
    
  def clickMethod(self, eventObj):
    """Used when the line on the canvas is clicked"""
    iface = self.interface
    if (iface.mode == 'rename') and (iface.nameEntry.get() not in [d.name for d in iface.durations]): #if we're in rename mode, and the new name isn't in use, then rename it
      self.setName(iface.nameEntry.get())
      iface.mode = 'select'
    elif iface.mode == 'select': #if we're in select mode, then prepare to move the duration
      if self.assocViewValue in [d.assocViewValue for d in iface.durations if d != self] != 0:
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
      iface.view.bind('<B1-Motion>', self.dragMethod) #bind the proc to change the value to the canvas

class Interface:
  """The class for the GUI interface"""
  
  viewWidth = 600 #width of the view canvas
  viewHeight = 200 #height of the view canvas

  def __init__(self):
#The root. This has to come first, because 'StringVar's and 'IntVar's in the 'View____'s need it to be initialized before they can be created.
    self.root = Tkinter.Tk()
    self.root.title('Qubit Control')
    
#the notebook has two pages, one for setup and one for the experiment
    self.noteBook = ttk.Notebook(self.root)
    self.noteBook.pack()
    self.setupTab = ttk.Frame(self.noteBook)
    self.experimentTab = ttk.Frame(self.noteBook)
    self.setupTab.pack()
    self.experimentTab.pack()
    #names for the tabs
    self.noteBook.add(self.setupTab, text='Setup')
    self.noteBook.add(self.experimentTab, text='Experiment')
    
#set some non-GUI variables
    self.mode = 'select' #mode determines what clikcing on the canvas will do. Options are 'select', 'addTime', 'deleteTime', and 'rename'
    
    #initialize these to None so that redrawAxisLabels knows to do its thing
    self.startValue = None
    self.endValue = None
    self.maxY = None
    
    self.start = ViewTime('Start',0.0,True,self)
    self.end = ViewTime('Stop',1000.0,True,self)
    initialValue = ViewValue('Initial',1,False,self)
    self.times = [self.start, self.end]
    self.values = [initialValue]
    self.durations = [ViewDuration('Initial',self.start,self.end,initialValue,self)]
    
#The control frame
    self.controlFrame = ttk.Labelframe(self.experimentTab, text='Controls')
    self.controlFrame.grid(column=0,row=1,columnspan=2,sticky='nsew',padx=5,pady=5)
   
    def addTimeMode():
      self.mode = 'addTime'
      self.nameEntry.focus_set() #move focus to nameEntry box when clicked
    ttk.Button(self.controlFrame, text='Add Time', command=addTimeMode).grid(column=0, row=0,sticky='w', padx=5, pady=5)
 
    def deleteTimeMode():
      self.mode = 'deleteTime'
    ttk.Button(self.controlFrame, text='Delete Time', command=deleteTimeMode).grid(column=1, row=0, sticky='w', padx=5, pady=5)

    def renameMode():
      self.mode = 'rename'
      self.nameEntry.focus_set() #move focus to nameEntry box when clicked
    ttk.Button(self.controlFrame, text='Rename', command=renameMode).grid(column=2, row=0, sticky='w', padx=5, pady=5)

    ttk.Label(self.controlFrame, text="Name:").grid(column=3, row=0, sticky='e', padx=5, pady=5)
    
    self.nameEntry = ttk.Entry(self.controlFrame)
    self.nameEntry.grid(column=4, row=0,sticky='w', padx=5, pady=5)

#The view frame and canvas
    self.axisLables = []

    self.viewFrame = ttk.Labelframe(self.experimentTab,text='SRAM View')
    self.viewFrame.grid(column=0,row=0,columnspan=2,sticky='nsew',padx=5,pady=5)

    self.view = Tkinter.Canvas(self.viewFrame, width=self.viewWidth, height=self.viewHeight) #todo: make array so that we can have more than one view
    self.view.grid(column=1, row=0, columnspan=3, rowspan=3, sticky='nsew', padx=5, pady=5)
  
    def canvasClick(eventObj):
      if (self.mode == 'addTime') and (self.nameEntry.get() not in [t.name for t in self.times]):
	time = self.xToTime(eventObj.x)
	newTime = ViewTime(self.nameEntry.get(),time,False,self)
	self.times.append(newTime)
	toSplit = [d for d in self.durations if (d.start() < time) and (d.end() > time)].pop() #find the duration that's getting chopped by this
	self.durations.remove(toSplit) #remove the duration that's getting chopped by this
	self.durations.extend(toSplit.split(newTime)) #add the two new durations
	self.mode = 'select' #put back in select mode after adding one time
	self.refresh() #we've added a new time, so have to redraw canvas and values frame from scratch

    self.view.bind("<Button-1>",  canvasClick)  
    
    #make it so that, after dragging an element has ceased, the binding is reset so that further dragging won't move the element unless it gets clicked again first
    #we do this by binding to any motion on the canvas
    self.view.bind("<Motion>", lambda e: self.view.bind("<B1-Motion>", lambda e: None))
    
    self.redrawCanvas()
    self.redrawAxisLabels()   
    
#The value frame
    self.valueFrameParts = []

    self.valueFrame = ttk.Labelframe(self.experimentTab,text='Values')
    self.valueFrame.grid(column=2, row=0, sticky='nsew', rowspan=2, padx=5, pady=5)
    self.valueFrameParts = [] #will contain all the widgets in the value frame so that we can destroy them even after the object they belong to gets destroyed
    self.redrawValueFrame()
  
  def redrawValueFrame(self):
    """Completely redraws the value frame of the interace"""
    
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
    
    for el in self.durations:
      el.disp(row)
      row += 1
  
  def redrawCanvas(self):
    """Clears the canvas and redraws everything on it"""
    
    #first, clear everything off the canvas (but don't delete the canvas itself)
    self.view.delete('all')
    
    #next, draw all the ViewTimes
    for time in self.times:
      if (time.name != 'Start') and (time.name != 'Stop'): #don't display anything for start or stop times; that way they can't be edited through the canvas
	lineID = self.view.create_line(self.timeToX(time.value), 0, self.timeToX(time.value), self.viewHeight, width=2, dash='.') #draw the line
	self.view.tag_bind(lineID, "<Button-1>",  time.clickMethod) #bind the line to it's clickMethod so that it can be interacted with

    #next, draw all the ViewValues
    for value in self.values:
      lineID = self.view.create_line(0, self.valueToY(value.value), self.viewWidth, self.valueToY(value.value), width=1, fill='red', dash='.')
      self.view.tag_bind(lineID, "<Button-1>",  value.clickMethod)

    #finially, draw all the ViewDurations. Because this comes last, it's drawn over the ViewValues. That means that when you click a duration, you don't get the ViewValue underneath.
    for dur in self.durations:
      lineID = self.view.create_line(self.timeToX(dur.start()), self.valueToY(dur.value()), self.timeToX(dur.end()), self.valueToY(dur.value()), width=2, fill='red')
      self.view.tag_bind(lineID, "<Button-1>",  dur.clickMethod)
  
  def redrawAxisLabels(self):
    """Redraws the axis lables in the view frame"""
    
    #only redraw if something has changed
    if (self.startValue != self.start.value) or (self.endValue != self.end.value) or (self.maxY != self.maxValue()):
      for l in self.axisLables:
	l.destroy()
      
      self.axisLables = []
    
      #the next three lables are for the x axis
      self.startValue = self.start.value
      tmp = ttk.Label(self.viewFrame, text=str(self.startValue))
      tmp.grid(column=1, row=3, sticky='w', padx=0, pady=5)
      self.axisLables.append(tmp)
    
      tmp = ttk.Label(self.viewFrame, text='Time (UNITS???)')
      tmp.grid(column=2, row=3, sticky='ew', padx=0, pady=5)
      self.axisLables.append(tmp)
    
      self.endValue = self.end.value
      tmp = ttk.Label(self.viewFrame, text=str(self.endValue))
      tmp.grid(column=3, row=3, sticky='e', padx=0, pady=5)
      self.axisLables.append(tmp)
    
      #next three lables are for y axis
      self.maxY = self.maxValue()
      tmp = ttk.Label(self.viewFrame, text=str(self.maxY))
      tmp.grid(column=0, row=0, sticky='ne', padx=0, pady=5)
      self.axisLables.append(tmp)
    
      tmp = ttk.Label(self.viewFrame, text='??? (UNITS???)')
      tmp.grid(column=0, row=1,sticky='nse', padx=0, pady=5)
      self.axisLables.append(tmp)
    
      tmp = ttk.Label(self.viewFrame, text = '0')
      tmp.grid(column=0, row=2,sticky='se', padx=0, pady=5)
      self.axisLables.append(tmp)
  
  def refresh(self):
    """Redraw all the parts of the GUI that can change"""
    self.redrawCanvas()
    self.redrawAxisLabels()
    self.redrawValueFrame()
    
  def maxValue(self):
    """Returns 1.25 times the value of the largest ViewValue so that the trace can be scaled directly on the canvas"""
    rawvalues =  [x.value for x in self.values]
    rawvalues.sort()
    return 1.25*rawvalues[-1] #return 1.25 times the largest value
  
  def maxTime(self):
    """Returns the time of the largest ViewTime"""
    return self.end.value
  
  def timeToX(self, time):
    """Coverts from time to canvas x coordinate"""
    return float(self.viewWidth)/self.maxTime() * time
  
  def valueToY(self, value):
    """Converts from value to canvas y coordinate"""
    return -float(self.viewHeight)/self.maxValue() * value + self.viewHeight
  
  def xToTime(self, x):
    """Converts from canvas x coordinate to time"""
    return float(self.maxTime())/self.viewWidth * x
  
  def yToValue(self, y):
    """Converts from canvas y coordinate to value"""
    return -self.maxValue()/self.viewHeight * y + self.maxValue()
  
  
if __name__ == "__main__":
  gui = Interface() #make the interace
  gui.root.mainloop() #set it in motion