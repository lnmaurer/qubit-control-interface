import ttk
import Tkinter
from qubit_views import *


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
        self.startTime = None
        self.endTime = None
        self.maxY = None
        self.minY = None
        self.updateMaxY = True #can make false to supress updating maxY; will make drawing faster
        self.updateMinY = True

        #to save typing '.interface' a bazillion times:
        self.timeToX = self.interface.timeToX
        self.xToTime = self.interface.xToTime
        self.viewWidth = self.interface.viewWidth
        self.viewHeight = self.interface.viewHeight
        self.start = self.interface.start
        self.end = self.interface.end    
    
        #creat a duration with the initial value
        self.durations = [ViewDuration('initial', self.start, self.end, initialValue, self.interface, self)]
    
        self.canvas = Tkinter.Canvas(self.viewFrame, width=self.interface.viewWidth, height=self.interface.viewHeight) #todo: make array so that we can have more than one view
        self.canvas.grid(column=1, row=0, columnspan=3, rowspan=3, sticky='nsew', padx=5, pady=5)
  
        self.canvas.bind("<Button-1>",  self.canvasClick)  
    
        #make it so that, after dragging an element has ceased, the binding is reset so that further dragging won't move the element unless it gets clicked again first
        #we do this by binding to any motion on any canvas
        self.canvas.bind("<Motion>", self.interface.clearCanvasBindings)
    
        self.redrawCanvas()
        self.redrawXaxis()
        self.redrawYaxis() 

    def toDict(self):
        """Retrurns a dict that describes this ViewTrace. For use in saving the experiment."""
        return {'name': self.name, 'durations': [d.toDict() for d in self.durations]}
    
    def redrawCanvas(self):
        """Clears the canvas and redraws everything on it"""
    
        self.redrawYaxis() #needed?
        self.updateMaxY = False #to speed up drawing
        self.updateMinY = False #to speed up drawing
    
        #first, clear everything off the canvas (but don't delete the canvas itself)
        self.canvas.delete('all')
    
        #next, draw a line for y=0 if it's in range
        yorig = self.valueToY(0)
        if (yorig >= 0) and (yorig <= self.interface.viewHeight):
            coords = [(self.timeToX(self.interface.start.time), yorig), (self.timeToX(self.interface.end.time), yorig)]
        self.canvas.create_line(*coords, width=1, fill='black', dash='-')
    
        #next, draw all the ViewValues
        for value in self.values():
            if value.mode == 'constant':
	        y = self.valueToY(value.maxValue())
	        lineID = self.canvas.create_line(0, y, self.viewWidth, y, width=1, fill='blue', dash='.')
            else:
	        times = self.interface.timeArray() #all times from start to end
	        coords = zip([self.timeToX(t) for t in times], [self.valueToY(v) for v in value.values(times)])
	        lineID = self.canvas.create_line(*coords, width=1, fill='green', dash='.') #draw ViewValues with functions in green
        self.canvas.tag_bind(lineID, "<Button-1>",  value.clickMethod)
 
        #next, draw all the ViewDurations. Because this comes after ViewValues, it's drawn over the ViewValues. That means that when you click a duration, you don't get the ViewValue underneath.
        for dur in self.durations:
            if dur.assocViewValue.mode == 'constant':
	        lineID = self.canvas.create_line(self.timeToX(dur.start()), self.valueToY(dur.value()), self.timeToX(dur.end()), self.valueToY(dur.value()), width=2, fill='red')
            else:
	        coords = zip([self.timeToX(t) for t in dur.times()], [self.valueToY(v) for v in dur.values()])
	        lineID = self.canvas.create_line(*coords, width=2, fill='red')
            self.canvas.tag_bind(lineID, "<Button-1>",  dur.clickMethod)

        #finally, draw all the ViewTimes; this mean's they're drawn over everything
        for time in self.interface.times:
            if (time.name != 'start') and (time.name != 'end'): #don't display anything for start or stop times; that way they can't be edited through the canvas
	        lineID = self.canvas.create_line(self.timeToX(time.time), 0, self.timeToX(time.time), self.viewHeight, width=2, dash='.') #draw the line
	        self.canvas.tag_bind(lineID, "<Button-1>",  time.clickMethod) #bind the line to it's clickMethod so that it can be interacted with

	  
        self.updateMaxY = True #reenable now that we're done drawing
        self.updateMinY = True
    
    def redrawXaxis(self):
        """Redraws the x-axis lables"""
    
        #only redraw if something has changed
        if (self.startTime != self.start.time) or (self.endTime != self.end.time):
            for l in self.xAxisLables:
	        l.destroy()
      
        self.xAxisLables = []
    
        self.startTime = self.start.time
        tmp = ttk.Label(self.viewFrame, text=str(self.startTime))
        tmp.grid(column=1, row=3, sticky='w', padx=0, pady=5)
        self.xAxisLables.append(tmp)
    
        tmp = ttk.Label(self.viewFrame, text='Time (ns)')
        tmp.grid(column=2, row=3, sticky='ew', padx=0, pady=5)
        self.xAxisLables.append(tmp)
    
        self.endTime = self.end.time
        tmp = ttk.Label(self.viewFrame, text=str(self.endTime))
        tmp.grid(column=3, row=3, sticky='e', padx=0, pady=5)
        self.xAxisLables.append(tmp)
  
    def redrawYaxis(self):
        """Redraws the y-axis lables"""
    
        #only redraw if the max value has changed; the bottom of the plot is always at zero
        if (self.maxY != self.maxValue()) or (self.minY != self.minValue()):
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
    
        self.minY = self.minValue()
        tmp = ttk.Label(self.viewFrame, text = str(self.minY))
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
        toSplit = find(lambda d: (d.start() < newTime.time) and (d.end() > newTime.time), self.durations)
        self.durations.remove(toSplit) #remove the duration that's getting chopped by this
        self.durations.extend(toSplit.split(newTime)) #add the two new durations
        self.redrawCanvas() #we've added a new time, so have to redraw canvas
     
    def deleteTime(self, viewTime):
        #plan: find the two durations that border this time, and delete one. Set the end time of the remaining one to the end time of the deleted one
        #todo: GIVE OPTION FOR WHICH OF THE TWO DURATIONS TO CHOOSE THE TIME FROM???
        firstDuration = self.durationEndingAt(viewTime)
        secondDuration = self.durationStartingAt(viewTime)
        firstDuration.endViewTime = secondDuration.endViewTime #change first duration so that it covers bother durations
        self.durations.remove(secondDuration) #get rid of second duration
     
    def maxValue(self):
        """Returns 1.25 times the value of the largest ViewValue so that the trace can be scaled directly on the canvas"""
        if self.updateMaxY: #only run if it's true
            rawvalues =  [d.maxValue() for d in self.durations]
            rawvalues.sort()
            maxValue = rawvalues[-1]
            if maxValue == 0:
	        return 1.0 #returning zero would result in divide by zero errors later
            else:
	        return 1.25*maxValue #return 1.25 times the largest value
        else: #otherwise, just return the old value
            return self.maxY

    def minValue(self):
        """Returns 1.25 times the value of the smallest ViewValue or zero (whichever is smaller) so that the trace can be scaled directly on the canvas"""
        if self.updateMinY: #only run if it's true
            rawvalues =  [d.minValue() for d in self.durations]
            rawvalues.sort()
            minValue = rawvalues[0]
            if minValue >= 0.0:
	        return 0.0
            else:
	        return 1.25*minValue
        else: #otherwise, just return the old value
            return self.minY
      
    def valueToY(self, value):
        """Converts from value to canvas y coordinate"""
        return float(self.interface.viewHeight)/(self.minValue()-self.maxValue()) * (value - self.maxValue())
    
    def yToValue(self, y):
        """Converts from canvas y coordinate to value"""
        return (self.minValue()-self.maxValue())/self.interface.viewHeight * y + self.maxValue() 
    
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
