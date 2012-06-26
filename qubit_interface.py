import Tkinter, tkFileDialog
import ttk
import yaml
import labrad
import tkMessageBox
import sys
from math import *
from twisted.internet.error import ConnectionRefusedError
from qubit_views import *
from qubit_traces import *

class Interface:
    """The class for the GUI interface"""
  
    viewWidth = 500 #width of the view canvas
    viewHeight = 100 #height of the view canvas

    def __init__(self):
        #The LabRAD connection
        self.labRADconnection = None #don't connect until later

        #Will hold the variables for executing code
        self.variables = globals().copy()    
    
        #The root. This has to come before the other GUI stuff, because 'StringVar's and 'IntVar's in the 'View____'s need it to be initialized before they can be created.
        self.root = Tkinter.Tk()
        self.root.title('Qubit Command Center')
        self.root.geometry('+3+10')

        #set some variables used by the GUI
        self.mode = 'select' #mode determines what clikcing on the canvas will do. Options are 'select', 'addTime', 'deleteTime', 'merge', 'newValue', and 'rename'

   
        #The menubar and menus
        menubar = Tkinter.Menu(self.root)
    
        #the file menu
        self.filemenu = Tkinter.Menu(menubar, tearoff=0)
        self.filemenu.add_command(label="New Experiment", accelerator="Ctrl+N", state='disabled', command=self.newExperiment)
        self.filemenu.add_command(label="Save Experiment As", accelerator="Ctrl+S", state='disabled', command=self.saveExperiment)
        self.filemenu.add_command(label="Load Experiment", accelerator="Ctrl+O", state='disabled', command=self.loadExperiment)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit)
        #bind keys to the actions
        self.root.bind_all('<Control-s>', lambda arg: self.saveExperiment()) #todo: disable before the experiment tab is populated
        self.root.bind_all('<Control-o>', lambda arg: self.loadExperiment()) #todo: disable before the experiment tab is populated
        self.root.bind_all('<Control-q>', lambda arg: self.root.quit())
        menubar.add_cascade(label="File", menu=self.filemenu)
    
        #the edit menu
        editmenu = Tkinter.Menu(menubar, tearoff=0)
        editmenu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.noteBook.event_generate('<Control-x>'))
        editmenu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.noteBook.event_generate('<Control-c>'))
        editmenu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.noteBook.event_generate('<Control-v>'))
        menubar.add_cascade(label="Edit", menu=editmenu)
        self.root.config(menu=menubar)

	#the notebook has two pages, one for setup and one for the experiment
        self.noteBook = ttk.Notebook(self.root)
        self.noteBook.pack()
        self.settingsTab = ttk.Frame(self.noteBook)
        self.settingsTab.pack()
        self.commandTab = ttk.Frame(self.noteBook)
        self.commandTab.pack()
        #names for the tabs
        self.noteBook.add(self.settingsTab, text='Settings')
        self.noteBook.add(self.commandTab, text='Command')
    
	

        #   Settings Tab
        #button to connect to manager
        def connectToManager():
            try:
	            self.labRADconnection = labrad.connect(self.managerAddress.get(),
					      port=int(self.managerPort.get()),
					      password=self.managerPassword.get())
            except ConnectionRefusedError as (err): #this error gets raised if we can't connect
            	tkMessageBox.showerror("Connection Error", err)
            else: #no error, so show what servers are connected
		serverListbox.delete(0, Tkinter.END) #if the listbox is already populated, clear it, this is unnescessary at present
	        serverListbox.insert(0,"<None>")
            for serverName in str(self.labRADconnection.servers).rsplit("\n"):
                serverListbox.insert(Tkinter.END, serverName) #add all the server names to the listbox
   
        #self.default = ttk.Button(self.commandTab, text = 'Default experiment', command=self.populateExperimentTab).grid(column=1,row=1, sticky='nsew')

	#the manager address entry
	ttk.Label(self.settingsTab, text='Manager address:').grid(column=0, row=0, sticky='e', padx=5, pady=5)
	self.managerAddress = Tkinter.StringVar()
	self.managerAddress.set('localhost') #todo: read out of a config file that saves previous entry
	ttk.Entry(self.settingsTab, textvariable=self.managerAddress).grid(column=1, row=0, sticky='w', padx=5, pady=5)   

	#the manager port entry
        ttk.Label(self.settingsTab, text='Manager port:').grid(column=0, row=1, sticky='e', padx=5, pady=5)
	self.managerPort = Tkinter.StringVar()
        self.managerPort.set('7682') #todo: read out of a config file that saves previous entry
	ttk.Entry(self.settingsTab, textvariable=self.managerPort).grid(column=1, row=1, sticky='w', padx=5, pady=5)
    
        #the manager password
	ttk.Label(self.settingsTab, text='Manager password:').grid(column=0, row=2, sticky='e', padx=5, pady=5)
        self.managerPassword = Tkinter.StringVar()
	self.managerPassword.set('test') #todo: read out of a config file that saves previous entry
        ttk.Entry(self.settingsTab, textvariable=self.managerPassword, show='*').grid(column=1, row=2, sticky='w', padx=5, pady=5)
    
	#the listbox that will show the available servers
        ttk.Label(self.settingsTab, text='Available Servers:').grid(column=2, row=0, sticky='s', padx=30, pady=5)
	serverListbox = Tkinter.Listbox(self.settingsTab, height=8, selectmode=Tkinter.MULTIPLE) #todo: is there now ttk version of this? NO
        serverListbox.grid(column=2, row=1, rowspan=8, sticky='n', padx=0, pady=5)
	serverListbox.insert(0,"<None>")
        scrollbar = ttk.Scrollbar(self.settingsTab, orient=Tkinter.VERTICAL, command=serverListbox.yview)
	scrollbar.grid(column=3, row=1, rowspan=8, sticky='nsw', padx=0, pady=5)
        serverListbox.configure(yscrollcommand=scrollbar.set)
    
	ttk.Button(self.settingsTab, text='Connect', command=connectToManager).grid(column=1, row=3,sticky='nsew', padx=5, pady=5)
        ttk.Button(self.settingsTab, text='Quit', command=self.root.quit).grid(column=1, row=4, sticky='nsew', padx=5, pady=5)
        
        
        #   Experiment Tab
        def runOnce():
            return
        
        def newSweep():
            return

        def loadSweep():
            return

        def runSweep():
            return

        def stopSweep():
            return

        def stopSweepSave():
            return

        ttk.Label(self.commandTab, text='Current Experiment: ').grid(column=0,row=0,padx=5, pady=5) 

        ttk.Button(self.commandTab, text = 'New experiment',command = self.newExperiment).grid(column=0,row=1, sticky='nsew',padx=5,pady=5)
        ttk.Button(self.commandTab, text = 'Open experiment',command = self.loadExperiment).grid(column=1,row=1, sticky='nsew',padx=5,pady=5)
        
        self.exp_param = ttk.Labelframe(self.commandTab, text='Experiment Parameters')
        self.exp_param.grid(column=0,row=2,sticky='nsew',padx=5,pady=5,columnspan=3)
        ttk.Label(self.exp_param, text='Stuff').grid(column=0,row=0)
        
        self.data_param= ttk.Labelframe(self.commandTab, text='Data Parameters')
        self.data_param.grid(column=0,row=3,sticky='nsew',padx=5,pady=5,columnspan=3)
        ttk.Label(self.data_param, text='More Stuff').grid(column=0,row=0)
        
        ttk.Button(self.commandTab, text ='Run Once',command=runOnce).grid(column=0,row=4,sticky='nsew',padx=5,pady=5)
       

        self.sweeps = ttk.Labelframe(self.commandTab, text ='Sweeps') 
        self.sweeps.grid(column=0,row=4,padx=5,pady=5,columnspan=3)
        ttk.Button(self.sweeps, text ='New Sweep',command=newSweep).grid(column=0,row=0,sticky='nsew',padx=5,pady=5)
        ttk.Button(self.sweeps, text ='Load Sweep',command=loadSweep).grid(column=1,row=0,sticky='nsew',padx=5,pady=5)
    
        ttk.Button(self.sweeps, text ='Run Sweep',command=runSweep,state='disabled').grid(sticky='nsew',padx=5,pady=5,column=0,row=1)
        ttk.Button(self.sweeps, text ='Stop Sweep',command=runSweep,state='disabled').grid(column=1,row=1,sticky='nsew',padx=5,pady=5)
        ttk.Button(self.sweeps, text ='Stop & Save Sweep',command=runSweep,state='disabled').grid(column=2,row=1,sticky='nsew',padx=5,pady=5)

        ttk.Label(self.commandTab, text ='Save Path:').grid(column=0,row=7,padx=5,pady=5)
        
        
        '''
	makeTracesButton = ttk.Button(self.settingsTab, text='make traces for selected', state='disabled', command=makeTraces)
        makeTracesButton.grid(column=2, row=9, sticky='n', padx=5, pady=5)
   

	def norm(self):
	    makeTracesButton.config(state='normal')
        serverListbox.bind('<<ListboxSelect>>',norm)
        '''
    
    def newExperiment(self):
        newExp = Tkinter.Toplevel(self.root)
        
        def cancel():
            newExp.destroy()
        
        #cancelb = ttk.Button(newExp,text="Cancel",command = cancel).grid(row='0',column='0')
        tr = ttk.Label(newExp,text='Number of sequencers:').grid(column='0',row='1')
        numSeqs = ttk.Entry(newExp)
        numSeqs.grid(column='1',row='1')
        ''' 
        filename = tkFileDialog.asksaveasfilename(filetypes=[('Qubit Experiment File','*.qbexp')], title="New experiment name")
        if fileName != '': #'' is returned if the user hits cancel
            f = open(fileName, 'w')
            f.write(yaml.dump(self.toDict()))
            f.close()
        '''
 
    def saveExperiment(self):
        """Saves the experiment to a file using a dialog box and YAML."""
        fileName = tkFileDialog.asksaveasfilename(filetypes=[('Qubit Experiment File','*.qbexp')], title="Save experiment as...")
        if fileName != '': #'' is returned if the user hits cancel
            f = open(fileName, 'w')
            f.write(yaml.dump(self.toDict()))
            f.close()
    
    
    def loadExperiment(self):
        """Loads the experiment from a file using a dialog box and YAML"""
        fileName = tkFileDialog.askopenfilename(filetypes=[('Qubit Experiment File','*.qbexp')], title="Open experiment...")
    
        if fileName != '': #'' is returned if the user hits cancel
            #load the information from the file
            f = open(fileName, 'r')
            loaded = yaml.load(f)
            f.close()
  
        #first, make the times
        self.times = []
        for time in loaded['times']:
	    t = ViewTime(time['name'], time['time'], time['locked'], self)
	    self.times.append(t)
	    #if it's start or end, take special care of it
	    if t.name == 'start':
	        self.start = t
	    elif t.name == 'end':
	        self.end = t
	
        #next, handle the values
        self.values = []
        for value in loaded['values']:
	    v = ViewValue(value['name'], value['value'], value['locked'], self, mode = value['mode'], functionText = value['functionText'])
	    self.values.append(v)
  
        #finally take care of the traces and their durations
        #todo: only have this work if the trace names match up with the already existing trace names
        self.traces = []
        row = 0
        initialValue0 = ViewValue('initial',1,False,self) #temp value for setting up traces
        for trace in loaded['traces']:
	    t = ViewTrace(trace['name'], self, row, initialValue0)
	    self.traces.append(t)
	    row = row + 1
	
	    t.durations = [] #an initial duration is made when the trace is created; get rid of it
	    for duration in trace['durations']:
	        dur = ViewDuration(duration['name'], self.timeNamed(duration['start']), self.timeNamed(duration['end']), self.valueNamed(duration['value']), self, t, locked=duration['locked'])
	        t.durations.append(dur)
	
        #add the variables in to our dictionary; apparently this is the cleanest way to do this
        self.variables = dict(self.variables.items() + loaded['variables'].items())

        #put the code back in the code box
        self.codeText.insert('end', loaded['code'])
      
        #now that we've loaded the data, refresh the GUI
        self.refresh()
    '''
    def populateExperimentTab(self):
        """Populates the experiment tab with widgets; call after deciding what servers we want traces for"""
        
        #enable experiment loading and saving
        self.filemenu.entryconfigure('Save Experiment As', state="normal")    
        self.filemenu.entryconfigure('Load Experiment', state="normal")    
    
        #initial conditions for the traces
        self.start = ViewTime('start',0.0,True,self)
        self.end = ViewTime('end',1000.0,True,self)
        initialValue0 = ViewValue('initial_0',1,False,self)
        initialValue1 = ViewValue('initial_1',1,False,self)
        self.times = [self.start, self.end]
        self.values = [initialValue0,initialValue1]
    
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

        def newValueMode():
            self.mode = 'newValue'
            self.nameEntry.focus_set() #move focus to nameEntry box when clicked
            ttk.Button(self.controlFrame, text='New Value', command=newValueMode).grid(column=4, row=0, sticky='w', padx=5, pady=5)

      
        #now, for the name label and entry
        ttk.Label(self.controlFrame, text="Name:").grid(column=5, row=0, sticky='e', padx=5, pady=5)
    
        self.nameEntry = ttk.Entry(self.controlFrame)
        self.nameEntry.grid(column=6, row=0, sticky='w', padx=5, pady=5)

        #The view frame and traces
        #print [int(i) for i in self.serverListbox.curselection()]
        self.viewFrame = ttk.Labelframe(self.experimentTab,text='Traces')
        self.viewFrame.grid(column=0,row=0,sticky='nsew',padx=5,pady=5)

        self.traces = []
    
        #todo: populate self.traces correctly
        self.traces.append(ViewTrace('test', self, 0, initialValue0))
        self.traces.append(ViewTrace('test2', self, 1, initialValue1))
    
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
            #'variables' is the dictionary that will hold the variables for executing the code
            self.variables = globals().copy() #start by just copying the global variables
            for time in self.times:
	        self.variables[time.name] = time #add all the times to variables
            for value in self.values:
        	self.variables[value.name] = value #add all the values to variables
        #execute the code now that we've made the dictionary
        try:
	    exec self.codeText.get('1.0', 'end') in self.variables
        except:
	    #todo: better message
	    tkMessageBox.showerror("Error", "{!s}\n{!s}\n{!s}".format(*sys.exc_info()))
            self.redrawValueFrame() #so that we display any numeric variables in the code that has been run
      
        ttk.Button(self.codeFrame, text='Run Code', command=runCode).grid(column=1, row=2, padx=5, pady=5)
        ttk.Button(self.codeFrame, text='Load Code').grid(column=2, row=2, padx=5, pady=5)
    
    def redrawValueFrame(self):
        """Completely redraws the value frame of the interface"""
        self.experimentTab.selection_clear()
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

        #next, we display all the ViewDurations. A heading label comes first.
        tmp = ttk.Label(self.valueFrame, text="Durations")
        tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
        self.valueFrameParts.append(tmp)    
        row +=1
    
        for el in self.durations():
            el.disp(row)
            row += 1
      
        #finally, display the numeric variables from any executed code
        tmp = ttk.Label(self.valueFrame, text="Numeric Variables")
        tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
        self.valueFrameParts.append(tmp)    
        row +=1
    
        for varName in self.variables:
            #only display if it's not in globals and it's numeric
            if (varName not in globals()) and isinstance(self.variables[varName], (int, long, float, complex)):
	        tmp = ttk.Label(self.valueFrame, text=varName + ': ' + str(self.variables[varName]))
	        tmp.grid(column=0, row=row, columnspan=2, padx=5, pady=5)
	        self.valueFrameParts.append(tmp)
	        #having the following work is kind of tricky; the default parameter in the lambda is critical. See <http://mail.python.org/pipermail/tutor/2005-November/043360.html>
	        tmp = ttk.Button(self.valueFrame, text='Delete', command=lambda vn=varName: self.deleteVar(vn))
	        tmp.grid(column=2, row=row, padx=5, pady=5)
	        self.valueFrameParts.append(tmp)
	        row +=1
 
  
    def deleteVar(self, varName):
        """Delete the variable named varName from the variable dictionary"""
        del self.variables[varName] #remove the variable from the dictionary
        self.redrawValueFrame()    
      
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
        return self.end.time
  
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
        self.timeNamed(nameString).setTime(newTime, True)
      
    def addTime(self, name=None, time=None, eventObject=None):
        """Adds a time, either given by a name and time, or by a click on the canvas and the name in the entry box. Then it updates the traces."""
        if eventObject != None: #then this addTime was in response to a click
            name = self.nameEntry.get()
            time = self.xToTime(eventObject.x)
            self.mode = 'select' #go back to select mode
    
        #todo: throw error if before start of after end
        if time <= self.start.time:
            pass
        if time >= self.end.time:
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
            tkMessageBox.showerror('Wrong!')

        elif viewTime == self.end:
            pass
        elif viewTime.locked:
            tkMessageBox.showerror('Wrong!')
    
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
        if value == None:
            raise NameError("There is no value named {}.".format(name))
        else:
            return value
    
    def traceNamed(self, name):
        """Returns the trace with the given name"""
        trace = find(lambda t: t.name == name, self.traces)
        if trace == None:
            raise NameError("There is no trace named {}.".format(name))
        else:
            return trace
      
    def timeArray(self):
        """Retruns array of all times, in 1ns steps, from start to end."""
        return range(self.start.time, self.end.time)
      
    def toDict(self):
        """Retrurns a dict that describes this Interface. For use in saving the experiment."""
        d = {}
        d['code'] = self.codeText.get('1.0', 'end')
        d['times'] = [t.toDict() for t in self.times]
        d['values'] = [v.toDict() for v in self.values]
        d['traces'] = [t.toDict() for t in self.traces]
        d['variables'] = {}
        #save all numeric variables that are in self.variables but not in globals(); those are the variables the user made
        for varName in self.variables:
            if (varName not in globals()) and isinstance(self.variables[varName], (int, long, float, complex)):
	        d['variables'][varName] = self.variables[varName]
        return d
    '''

