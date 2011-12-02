import Tkinter
import ttk

class ViewTime:
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
    if (self.value != value) and (not self.locked):
      sortedTimes =  [t.value for t in self.interface.times]
      sortedTimes.sort
      index = sortedTimes.index(self.value)
      
      #find the limits for what this time can be set to
      if index == 0: #self is the smallest time
	minTime = None
	maxTime = sortedTimes[index+1]
      elif index == (len(sortedTimes)-1): #self is the largest time
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
    self.stringVar.set(str(value))
  
  def setName(self, name):
    if self.name != name:
      self.name = name
      self.redraw()
  
  def disp(self, row):
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
    if self.row != None:
      self.disp(self.row)
  
  def dragMethod(self, eventObj):
    self.setValue(self.interface.xToTime(eventObj.x))
  
class ViewValue:
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
    if (self.value != value) and (not self.locked):
      self.value = value
      self.stringVar.set(str(value))
      
      self.interface.redrawCanvas()
      self.interface.redrawAxisLabels()
  
  def setName(self, name):
    if self.name != name:
      self.name = name
      self.redraw()
  
  def disp(self, row):
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
    if self.row != None:
      self.disp(self.row)
  
  def dragMethod(self,eventObj):
    self.setValue(self.interface.yToValue(eventObj.y))
  
class ViewDuration:
  def __init__(self, name, startViewTime, endViewTime, assocViewValue, interface, row=None):
    self.name = name
    self.startViewTime = startViewTime
    self.endViewTime = endViewTime
    self.assocViewValue = assocViewValue
    self.interface = interface
    self.row = row
   
    self.tkLabel = None
  
  def setName(self, name):
    if self.name != name:
      self.name = name
      self.redraw()  
  
  def setStartViewTime(self, startViewTime):
    self.startViewTime = startViewTime
    self.interface.redrawCanvas()
    self.redraw()

  def setEndViewTime(self, endViewTime):
    self.endViewTime = endViewTime
    self.interface.redrawCanvas()
    self.redraw()
  
  def setViewValue(self, viewValue):
    self.assocViewValue = viewValue
    self.interface.redrawCanvas()
    self.redraw()
  
  def disp(self, row):
    self.row = row
    labelText = self.name + ': ' + self.startViewTime.name + ' ' + self.endViewTime.name + ' ' + self.assocViewValue.name
    
    if self.tkLabel != None:
      self.tkLabel.destroy()

    self.tkLabel = ttk.Label(self.interface.valueFrame, text=labelText)
    self.tkLabel.grid(column=0, row=row, sticky='w', columnspan=3, padx=5, pady=5)
    self.interface.valueFrameParts.append(self.tkLabel)
  
  def redraw(self):
    if self.row != None:
      self.disp(self.row)
  
  def split(self, middleViewTime):
    [ViewDuration(self.name + ' part A',self.startViewTime,middleViewTime,self.assocViewValue,self.interface), ViewDuration(self.name + ' part B',middleViewTime,self.endViewTime,self.assocViewValue,self.interface)]
  
  def start(self):
    return self.startViewTime.value
  
  def end(self):
    return self.endViewTime.value
  
  def value(self):
    return self.assocViewValue.value
  
  def dragMethod(self,eventObj):
    self.assocViewValue.setValue(self.interface.yToValue(eventObj.y))
  
class Interface:

  viewWidth = 600
  viewHeight = 200

  def __init__(self):
#The root. This has to come first, because 'StringVar's and 'IntVar's in the 'View____'s need it to be initialized before they can be called.
    self.root = Tkinter.Tk()
    self.root.title('Qubit Control')
    
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
    self.controlFrame = ttk.Labelframe(self.root, text='Controls')
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

    self.viewFrame = ttk.Labelframe(self.root,text='SRAM View')
    self.viewFrame.grid(column=0,row=0,columnspan=2,sticky='nsew',padx=5,pady=5)

    self.view = Tkinter.Canvas(self.viewFrame, width=self.viewWidth, height=self.viewHeight) #todo: make array so that we can have more than one view
    self.view.grid(column=1, row=0, columnspan=3, rowspan=3, sticky='nsew', padx=5, pady=5)
  
    def canvasClick(eventObj):
      print eventObj.x, eventObj.y #todo: put the real thing in; this function is just a test
    self.view.bind("<Button-1>",  canvasClick)  
    
    #make it so that, after dragging an element has ceased, the binding is reset so that further dragging won't move the element unless it gets clicked again first
    #we do this by binding to any motion on the canvas
    self.view.bind("<Motion>", lambda e: self.view.bind("<B1-Motion>", lambda e: None))
    
    self.redrawCanvas()
    self.redrawAxisLabels()   
    
#The value frame
    self.valueFrameParts = []

    self.valueFrame = ttk.Labelframe(self.root,text='Values')
    self.valueFrame.grid(column=2, row=0, sticky='nsew', rowspan=2, padx=5, pady=5)
    self.valueFrameParts = [] #will contain all the widgets in the value frame so that we can destroy them even after the object they belong to gets destroyed
    self.redrawValueFrame()
  
  def redrawValueFrame(self):
    #first, clear out all the old stuff from the frame
    for l in self.valueFrameParts:
      l.destroy()
    
    self.valueFrameParts = [] #array to store the parts so that we can destroy them when redrawing the frame
    
    tmp = ttk.Label(self.valueFrame, text="Times")
    tmp.grid(column=0, row=0, columnspan=2, padx=5, pady=5)
    self.valueFrameParts.append(tmp)
    
    row = 1
    
    for el in self.times:
      el.disp(row)
      row += 1
    
    tmp = ttk.Label(self.valueFrame, text="Values")
    tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
    self.valueFrameParts.append(tmp)
    
    row +=1
    
    for el in self.values:
      el.disp(row)
      row += 1
    
    tmp = ttk.Label(self.valueFrame, text="Durations")
    tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
    self.valueFrameParts.append(tmp)    
    
    row +=1
    
    for el in self.durations:
      el.disp(row)
      row += 1
  
  def refresh(self):
    self.redrawCanvas()
    self.redrawAxisLabels()
    self.redrawValueFrame()
  
  def redrawCanvas(self):
    pass
  
  def redrawAxisLabels(self):
    #only update if something has changed
    if (self.startValue != self.start.value) or (self.endValue != self.end.value) or (self.maxY != self.maxValue):
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
    
  def maxValue(self):
    rawvalues =  [x.value for x in self.values]
    rawvalues.sort
    return 1.25*rawvalues[-1] #return 1.25 times the largest value
  
  def maxTime(self):
    return self.end.value
  
  def timeToX(self, time):
    return float(self.viewWidth)/self.maxTime * time
  
  def valueToY(self, value):
    return -float(self.ViewHeight)/self.maxValue * value + self.viewHeight
  
  def xToTime(self, x):
    return float(self.maxTime)/self.viewWidth * x
  
  def yToValue(self, y):
    return -self.maxValue/self.viewHeight * y + self.maxValue
  
  
if __name__ == "__main__":
  gui = Interface()
  gui.root.mainloop()