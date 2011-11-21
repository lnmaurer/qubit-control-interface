require 'tk'
require 'tkextlib/tile'

#todo, make deletable, make lockable so can't be deleted
class ViewTime
  attr_reader :value, :name, :locked, :parent, :row
  def initialize(name,value,locked,interface,parent=nil,row=nil)
    @name = name
    @value = value
    @tkVariable = TkVariable.new
    @tkVariable.value = @value
    @interface = interface
    @locked = locked
    @parent = parent
    @row = row
  end
  def value=(newValue)
    if (@value != newValue) and (not @locked)
      sortedTimes = @interface.times.collect{|t| t.value}.sort
      currentTime = @value
      maxTime = sortedTimes.find{|t| t > currentTime} #finds the smallest time larger than currentTime
      minTime = sortedTimes.reverse.find{|t| t < currentTime} #finds the largest time smaller than currentTime
      if ((maxTime == nil) and (newValue > minTime)) or #if we're changing the largest time, maxTime will be nil
	((minTime == nil) and (newValue < maxTime)) or #if we're changing the smallest time, minTime will be nil
	((maxTime != nil) and (minTime != nil) and (newValue > minTime) and (newValue < maxTime)) #the requested time is in (minTime,maxTime)
	@value = newValue
	@interface.redrawCanvas
	@interface.redrawAxisLabels
      end
      #by keeping this outside the previous if statement, the tkEntry is restored to the old value if an unacceptable value was entered
      #TODO: WHY DOES THIS CRASH SOMETIMES?
#       @tkVariable.value = @value
      #TODO: WHY DOES THIS WORK
      @tkVariable = TkVariable.new
      @tkVariable.value = @value
      @tkEntry.textvariable = @tkVariable
    end
  end
  def name=(newName)
    if @name != newName
      @name = newName
      self.redraw
    end
  end
  def disp(parent, row)
    @parent = parent
    @row = row
    entryProc = proc do
      if @tkEntry.get != ''
	self.value = @tkEntry.get.to_f 
	@interface.redrawCanvas
      end
      1
    end
    tempName = @name
    tempDependent = @locked
    self.destroyTk
    @tkLabel = Tk::Tile::Label.new(parent){
      text    "#{tempName}:"
    }.grid(:column=>0, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
    @tkEntry = Tk::Tile::Entry.new(parent){
#       validate		'focusout' #TODO: WHY DOES THIS ONLY WORK ONCE????
#       validatecommand	entryProc
    }.grid(:column=>1, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
    @tkEntry.state = (@locked ? 'readonly' : 'normal')
    @tkEntry.textvariable = @tkVariable
    @tkEntry.bind('Return',entryProc)
    
    #the checkbox handles locking the value
    checkProc = proc do
      @locked = (@tkCheck.get_value == '1')
      @tkEntry.state = (@locked ? 'readonly' : 'normal')
    end
    @tkCheck = Tk::Tile::CheckButton.new(parent) {
      text 'Locked?'
      command checkProc
    }.grid(:column=>2, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
    @tkCheck.set_value(@locked ? '1': '0')
  end
  def destroyTk
    @tkLabel.destroy if @tkLabel != nil
    @tkEntry.destroy if @tkLabel != nil
  end
  def redraw
    self.disp(@parent,@row) if @parent != nil and @row != nil
  end
end

class ViewValue
  attr_reader :value, :name, :locked, :parent, :row
  def initialize(name, value, locked, interface, parent=nil, row=nil)
    @name = name
    @value = value
    @tkVariable = TkVariable.new
    @tkVariable.value = @value
    @locked = locked
    @interface = interface
    @parent = parent
    @row = row
  end
  def value=(newValue)
    if (@value != newValue) and (not @locked)
      @value = newValue
#TODO: why does this crash sometimes?
#       @tkVariable.value = @value
#TODO: why does this work?
      @tkVariable = TkVariable.new
      @tkVariable.value = @value
      @tkEntry.textvariable = @tkVariable
      
      @interface.redrawCanvas
      @interface.redrawAxisLabels
    end
  end
  def name=(newName)
    if @name != newName
      @name = newName
      self.redraw
    end
  end
  def disp(parent, row)
    @parent = parent
    @row = row
    tempName = @name
    tempDependent = @locked
    entryProc = proc do
      if @tkEntry.get != ''
	self.value = @tkEntry.get.to_f 
	@interface.redrawCanvas
      end
      1
    end
    self.destroyTk
    @tkLabel = Tk::Tile::Label.new(parent){
      text    "#{tempName}:"
    }.grid(:column=>0, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
    @tkEntry = Tk::Tile::Entry.new(parent){
#       validate		'focusout' #TODO: WHY DOES THIS ONLY WORK ONCE????
#       validatecommand	entryProc
    }.grid(:column=>1, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
    @tkEntry.state = (@locked ? 'readonly' : 'normal')
    @tkEntry.textvariable = @tkVariable
    @tkEntry.bind('Return',entryProc)
    
    checkProc = proc do
      @locked = (@tkCheck.get_value == '1')
      @tkEntry.state = (@locked ? 'readonly' : 'normal')
    end
    @tkCheck = Tk::Tile::CheckButton.new(parent) {
      text 'Locked?'
      command checkProc
    }.grid(:column=>2, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
    @tkCheck.set_value(@locked ? '1': '0')
  end
  def destroyTk
    @tkLabel.destroy if @tkLabel != nil
    @tkEntry.destroy if @tkLabel != nil
  end
  def redraw
    self.disp(@parent,@row) if @parent != nil and @row != nil
  end
end

class ViewDuration
  attr_accessor :name,:startViewTime, :endViewTime, :assocViewValue, :parent, :row
  def initialize(name,startViewTime,endViewTime,assocViewValue,parent=nil,row=nil)
    @name = name
    @startViewTime = startViewTime
    @endViewTime = endViewTime
    @assocViewValue = assocViewValue
    @parent = parent
    @row = row
  end
  def name=(newName)
    if @name != newName
      @name = newName
      self.redraw
    end
  end
  def startViewTime=(s)
    @startViewTime = s
    self.redraw
  end
  def endViewTime=(e)
    @endViewTime = e
    self.redraw
  end
  def assocViewValue=(a)
    @assocViewValue = a
    self.redraw
  end  
  def disp(parent, row)
    @parent = parent
    @row = row
    tempName = @name
    startName = @startViewTime.name
    endName = @endViewTime.name
    valueName = @assocViewValue.name
    self.destroyTk
    @tkLabel = Tk::Tile::Label.new(parent){
      text    "#{tempName}: #{startName} #{endName} #{valueName}"
    }.grid(:column=>0, :row=>row,:sticky=>'w', :padx=>5, :pady=>5)
  end
  
  def destroyTk
    @tkLabel.destroy if @tkLabel != nil
  end
  
  def redraw
    self.disp(@parent,@row) if @parent != nil and @row != nil
  end
  
  def split(middleViewTime) #split a duration in to two durations
    [ViewDuration.new(@name + ' part A',@startViewTime,middleViewTime,@assocViewValue,@parent,@row), ViewDuration.new(@name + ' part B',middleViewTime,@endViewTime,@assocViewValue,@parent,@row)]
  end
    
  def start
    @startViewTime.value
  end
    
  def stop
    @endViewTime.value
  end
    
  def value
    @assocViewValue.value
  end
end

class Array
  def name_used?(name) #checks to see if name is already used in the list
    self.find{|el| el.name == name} != nil
  end
end

class Interface
  @@ViewWidth = 600
  @@ViewHeight = 200
  attr_reader :times
  def initialize
    @root = TkRoot.new(){title 'Qubit Control'}#.protocol('WM_DELETE_WINDOW', quit)
    
    @controlFrame = Tk::Tile::LabelFrame.new(@root,:text=>'Controls').grid(:column=>0,:row=>1,:columnspan=>2,:sticky=>'nsew',:padx=>5,:pady=>5)
    
    @mode = :select #mode determines what clikcing on the canvas will do. Options are :select, :addTime, :deleteTime, and :rename
    
    @startValue = 0
    @stopValue = 0
    @maxY = 0
    
    @start = ViewTime.new('Start',0.0,true,self)
    @end = ViewTime.new('Stop',1000.0,true,self)
    initialValue = ViewValue.new('Initial',1,false,self)
    @times = [@start, @end]
    @values = [initialValue]
    @durations = [ViewDuration.new('Initial',@start,@end,initialValue,nil)]

    #view frame
    @viewFrame = Tk::Tile::LabelFrame.new(@root,:text=>'SRAM View').grid(:column=>0,:row=>0,:columnspan=>2,:sticky=>'nsew',:padx=>5,:pady=>5)
    
    #make the canvas
    @view = TkCanvas.new(@viewFrame){ #TODO: make array so that we can have more than one view
      width @@ViewWidth
      height @@ViewHeight
    }.grid(:column=>1,:row=> 0, :columnspan=>3, :rowspan=> 3, :sticky=>'nsew', :padx=>5, :pady=>5)
      
    #what happens when the view is clicked with the left mouse button
    viewClick = proc do |canvasx, canvasy|
      if @mode == :addTime and (not @times.collect{|t| t.name}.include?(@nameEntry.get))
	time = xToTime(canvasx)
	newTime = ViewTime.new(@nameEntry.get,time,false,self)
	@times << newTime
	toSplit = @durations.find{|dur| (dur.start < time) and (dur.stop > time)} #find the duration that's getting chopped by this
	@durations.reject!{|dur| (dur.start < time) and (dur.stop > time)} #remove the duration that's getting chopped by this
	@durations.push(toSplit.split(newTime)).flatten! #add the two new durations
	@mode = :select #put back in select mode after adding one time
	self.refresh #we've added a new time, so have to redraw canvas and values frame from scratch
      end
    end
    @view.bind('1',  viewClick, "%x %y")
    
    #make it so that, after dragging an element has ceased, the binding is reset so that further dragging won't move the element unless it gets clicked again first
    #we do this by binding to any motion on the canvas
    @view.bind("Motion", proc{@view.bind('B1-Motion', proc{}, "%x %y")}, "%x %y")
    
    self.redrawCanvas
    self.redrawAxisLabels
    
    #value frame
    @valueFrame = Tk::Tile::LabelFrame.new(@root,:text=>'Values').grid(:column=>2,:row=>0,:sticky=>'nsew',:rowspan=>2,:padx=>5,:pady=>5)
    self.redrawValueFrame
    
    #control frame
    addTimeMode = proc {@mode = :addTime; @nameEntry.focus} #move focus to nameEntry box when clicked
    Tk::Tile::Button.new(@controlFrame) {
      text    'Add Time'
      command addTimeMode
    }.grid(:column=>0, :row=>0,:sticky=>'w', :padx=>5, :pady=>5)
    deleteTomeMode = proc {@mode = :deleteTime}
    Tk::Tile::Button.new(@controlFrame) {
      text    	'Delete Time'
      command	deleteTomeMode
    }.grid(:column=>1, :row=>0,:sticky=>'w', :padx=>5, :pady=>5)
    renameMode = proc {@mode = :rename; @nameEntry.focus} #move focus to nameEntry box when clicked
    Tk::Tile::Button.new(@controlFrame) {
      text    'Rename'
      command renameMode
    }.grid(:column=>2, :row=>0,:sticky=>'w', :padx=>5, :pady=>5)
    Tk::Tile::Label.new(@controlFrame){
      text    "Name:"
    }.grid(:column=>3, :row=>0,:sticky=>'e', :padx=>5, :pady=>5)
    @nameEntry = Tk::Tile::Entry.new(@controlFrame){
      textvariable    @addName
    }.grid(:column=>4, :row=>0,:sticky=>'w', :padx=>5, :pady=>5)
  end
  
  def redrawValueFrame
    #first, clear out all the old stuff from the frame
    @times.each{|t| t.destroyTk}
    @values.each{|v| v.destroyTk}
    @durations.each{|d| d.destroyTk}
    @lables.each{|l| l.destroy} if @lables != nil
    
    @lables = [] #array to store the lables so that we can destroy them when redrawing the frame
    
    @lables << Tk::Tile::Label.new(@valueFrame){
      text    "Times:"
    }.grid(:column=>0, :row=>0, :columnspan=>2, :sticky=>'ew', :padx=>5, :pady=>5)
    row = 1
    @times.each {|el| el.disp(@valueFrame,row); row += 1}
    
    @lables << Tk::Tile::Label.new(@valueFrame){
      text    "Values:"
    }.grid(:column=>0, :row=>row, :columnspan=>2, :sticky=>'ew', :padx=>5, :pady=>5)
    row +=1
    @values.each {|el| el.disp(@valueFrame,row); row += 1}
    
    @lables << Tk::Tile::Label.new(@valueFrame){
      text    "Durations:"
    }.grid(:column=>0, :row=>row, :columnspan=>2, :sticky=>'ew', :padx=>5, :pady=>5)
    row +=1
    @durations.each {|el| el.disp(@valueFrame,row); row += 1}
  end
  
  def refresh
    self.redrawCanvas
    self.redrawAxisLabels
    self.redrawValueFrame
  end
  
  def redrawCanvas
    #clean off the canvas
    @view.delete('all')
    
    @times.each do |time|
      unless time.name == 'Start' or time.name == 'Stop'
	tempProc = proc do |canvasx, canvasy|
	  if @mode == :rename
	    time.name = @nameEntry.get unless @times.collect{|t| t.name}.include?(@nameEntry.get)
	    @mode = :select
	  elsif @mode == :select
	    tempDragProc = proc do |canvasx, canvasy|
	      value = xToTime(canvasx)
	      time.value = value
	    end
	    @view.bind('B1-Motion', tempDragProc, "%x %y") 
	  elsif @mode == :deleteTime
	    #plan: find the two durations that border this time, and delete one. Set the end time of the remaining one to the end time of the deleted one
	    #TODO: GIVE OPTION FOR WHICH OF THE TWO DURATIONS TO CHOOSE THE VALUE FROM
	    firstDuration = @durations.find{|d| d.endViewTime == time}
	    secondDuration = @durations.find{|d| d.startViewTime == time}
	    firstDuration.endViewTime = secondDuration.endViewTime
	    @durations.delete(secondDuration) #get rid of second duration
	    @times.delete(time) #get rid of the deleted time
	    unless @durations.find{|d| d.assocViewValue == secondDuration.assocViewValue} != nil #there's another duration using that value, so we don't want to delete the value
	      @values.delete(secondDuration.assocViewValue)
	    end
self.redrawCanvas #TODO: integrate in to class
	    @mode = :select
	  end
	end
	temp = TkcLine.new(@view, timeToX(time.value), 0, timeToX(time.value), @@ViewHeight, :width =>2, :dash=>'.')
	temp.bind('1',  tempProc, "%x %y")
      end
    end
   
    @values.each do |val|
      tempProc = proc do |canvasx, canvasy|
	if @mode == :rename
	  newName = @nameEntry.get #the new name
	  replacementValue = @values.find{|v| v.name == newName} #look and see if any other value already has this name
	  if replacementValue != nil #does a value with this name already exist?
	    #if the named value does exist, we'll get rid of the current value and replace it everywhere with the named value	    
	    @values.reject!{|v| v == val} #get rid of the current value from the list
	    @durations.find_all{|dir| dir.assocViewValue == val}.each{|dir| dir.assocViewValue = replacementValue} #find all the durations that use the value in question, and replace them
	    self.refresh #the number of values has changed, so need to redraw values frame from scratch
	  else #no value uses that name
	    val.name = newName #if no value with this name already exists, merely change the name
	  end
	  @mode = :select
	elsif @mode == :select
	  tempDragProc = proc do |canvasx, canvasy|
	    value = yToValue(canvasy)
	    val.value = value
	  end
	  @view.bind('B1-Motion', tempDragProc, "%x %y")	  
	end
      end
      temp = TkcLine.new(@view, 0, valueToY(val.value), @@ViewWidth, valueToY(val.value), :width =>1, :fill=>'red', :dash=>'.')
      temp.bind('1',  tempProc, "%x %y")
    end    
    
    @durations.each do |dur|
      #the following proc will get called if we click on a duration
      tempProc = proc do |canvasx, canvasy|
	if @mode == :rename #if we're in rename mode, then rename it
	  dur.name = @nameEntry.get unless @durations.collect{|t| t.name}.include?(@nameEntry.get)
	  @mode = :select
	elsif @mode == :select #if we're in select mode, then prepare to move the duration
	  if @durations.find{|d| (d.assocViewValue == dur.assocViewValue) and not (d == dur)} #more than one other duration uses this value
	    #need to make a new value and come up with a unique name for it; we'll take the name and stick a number on the end. First, find a number that will give a unique name
	    count = 1 #count holds the number we'll append to the end of the name
	    while @values.collect{|v| v.name}.include?(dur.assocViewValue.name + count.to_s)
	      count += 1
	    end
	    newValue = ViewValue.new(dur.assocViewValue.name + count.to_s, dur.assocViewValue.value, dur.assocViewValue.locked,self)
	    @values << newValue
	    dur.assocViewValue = newValue
	    self.redrawValueFrame #added a new thing to value frame, so need to redraw it from scratch
	  end
	  #the folllwing proc and binding allows the duration's value to be changed. We need to bind to the canvas. Binding to the duration's line alone doesn't cut it; the mouse will move off the line before the refresh and it'll stop working.
	  tempDragProc = proc do |canvasx, canvasy|
	    value = yToValue(canvasy)
	    dur.assocViewValue.value = value
	  end
	  @view.bind('B1-Motion', tempDragProc, "%x %y")
	end
      end
      temp = TkcLine.new(@view, timeToX(dur.start), valueToY(dur.value), timeToX(dur.stop), valueToY(dur.value), :width =>2, :fill=>'red')
      temp.bind('1',  tempProc, "%x %y")
    end
  end
  
  def redrawAxisLabels
    return if (@startValue == @start.value.to_s) and (@endValue == @end.value.to_s) and (@maxY == maxValue.to_s) #don't do anything if nothing here needs updating
    
    @axisLables.each{|l| l.destroy} if @axisLables != nil
    @axisLables = []
    
    #the next three lables are for the x axis
    startValue = @startValue = @start.value.to_s
    @axisLables << Tk::Tile::Label.new(@viewFrame){
	text    startValue
    }.grid(:column=>1, :row=>3,:sticky=>'w', :padx=>0, :pady=>5)
    @axisLables << Tk::Tile::Label.new(@viewFrame){
	text    'Time (UNITS???)'
    }.grid(:column=>2, :row=>3,:sticky=>'ew', :padx=>0, :pady=>5)
    endValue = @endValue = @end.value.to_s
    @axisLables << Tk::Tile::Label.new(@viewFrame){
	text    endValue
    }.grid(:column=>3, :row=>3,:sticky=>'e', :padx=>0, :pady=>5)
    
    #next three lables are for y axis
    maxY = @maxY = maxValue.to_s
    @axisLables << Tk::Tile::Label.new(@viewFrame){
	text    maxY
    }.grid(:column=>0, :row=>0,:sticky=>'ne', :padx=>0, :pady=>5)
    @axisLables << Tk::Tile::Label.new(@viewFrame){
	text    '??? (UNITS???)'
    }.grid(:column=>0, :row=>1,:sticky=>'nse', :padx=>0, :pady=>5)
    @axisLables << Tk::Tile::Label.new(@viewFrame){
	text    '0'
    }.grid(:column=>0, :row=>2,:sticky=>'se', :padx=>0, :pady=>5)
  end
  
  def maxValue
    1.25*@values.collect{|el| el.value}.sort.last
  end
  
  def maxTime
    @end.value
  end
  
  def timeToX(time)
    @@ViewWidth.to_f/self.maxTime*time
  end
  
  def valueToY(value)
    -@@ViewHeight.to_f/self.maxValue*value + @@ViewHeight
  end
  
  def xToTime(x)
    self.maxTime.to_f/@@ViewWidth*x
  end
  
  def yToValue(y)
    -self.maxValue/@@ViewHeight*y + self.maxValue
  end
end

if __FILE__ == $0
  $gui = Interface.new
  Tk.mainloop()
end
    