import Tkinter
import ttk

class ViewTime:
  def __init__(self, name, value, locked, interface, row=None):
    self.name = name
    self.value = value
    self.locked = locked
    self.interface = interface
    self.row = row
  
  def setValue(self, value):
    pass
  
  def setName(self, name):
    pass
  
  def disp(self, row):
    pass
  
  def redraw(self):
    pass
  
  def dragMethod(self):
    pass
  
class ViewValue:
  def __init__(self,name, value, locked, interface, row=None):
    self.name = name
    self.value = value
    self.locked = locked
    self.interface = interface
    self.row = row
  
  def setValue(self, value):
    pass
  
  def setName(self, name):
    pass
  
  def disp(self, row):
    pass
  
  def redraw(self):
    pass
  
  def dragMethod(self):
    pass
  
class ViewDuration:
  def __init__(self,name,startViewTime,endViewTime,assocViewValue,interface,row=None):
    self.name = name
    self.startViewTime = startViewTime
    self.endViewTime = endViewTime
    self.assocViewValue = assocViewValue
    self.interface = interface
    self.row = row
  
  def setStartViewTime(self, startViewTime):
    pass

  def setEndViewTime(self, endViewTime):
    pass
  
  def setViewValue(self, viewValue):
    pass
    
  def setName(self, name):
    pass
  
  def disp(self, row):
    pass
  
  def redraw(self):
    pass
  
  def split(self, middleViewTime):
    pass
  
  def start(self):
    pass
  
  def end(self):
    pass
  
  def value(self):
    pass
  
  def dragMethod(self):
    pass
  
class Interface:

  viewWidth = 600
  viewHeight = 200

  def __init__(self):
    #first, set some non-GUI variables
    self.mode = 'select' #mode determines what clikcing on the canvas will do. Options are 'select', 'addTime', 'deleteTime', and 'rename'
    
    self.startValue = 0
    self.stopValue = 0
    self.maxY = 0
    
    self.start = ViewTime('Start',0.0,True,self)
    self.end = ViewTime('Stop',1000.0,True,self)
    initialValue = ViewValue('Initial',1,False,self)
    self.times = [self.start, self.end]
    self.values = [initialValue]
    self.durations = [ViewDuration('Initial',self.start,self.end,initialValue,self)]
    
    #The root
    self.root = Tkinter.Tk()
    self.root.title('Qubit Control')
    
    #The control frame
    self.controlFrame = ttk.Labelframe(self.root, text='Controls')
    self.controlFrame.grid(column=0,row=1,columnspan=2,sticky='nsew',padx=5,pady=5)

    #The view frame and canvas
    self.viewFrame = ttk.Labelframe(self.root,text='SRAM View')
    self.viewFrame.grid(column=0,row=0,columnspan=2,sticky='nsew',padx=5,pady=5)

    self.view = Tkinter.Canvas(self.viewFrame, width=self.viewWidth, height=self.viewHeight) #todo: make array so that we can have more than one view
    self.view.grid(column=1, row=0, columnspan=3, rowspan=3, sticky='nsew', padx=5, pady=5)
  
    def canvasClick(eventObj):
      print eventObj.x, eventObj.y #todo: put the real thing in; this is just a test
    self.view.bind("<Button-1>",  canvasClick)  
  
  def redrawValueFrame(self):
    pass
  
  def refresh(self):
    pass
  
  def redrawCanvas(self):
    pass
  
  def redrawAxisLabels(self):
    pass
  
  def maxValue(self):
    pass
  
  def maxTime(self):
    pass
  
  def timeToX(self, time):
    pass
  
  def valueToY(self, value):
    pass
  
  def xToTime(self, x):
    pass
  
  def yToValue(self, y):
    pass
  
  
if __name__ == "__main__":
  gui = Interface()
  gui.root.mainloop()