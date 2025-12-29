import time

class Labeler:
    """ Class for labeling the dataset """
    def __init__(self, labelList = None):
        # set current label index to zero
        self.currentLabelIndex = 0
        # inactivate label stream functionality
        self.labelStreamerActive = False
        self.streamerCurrentTime = None
        # initialize labels list
        if not labelList:
            self.labelList = []
        else:
            self.labelList = labelList
    
    def getLabels(self):
        """
        Get the current list of labels.
        
        Parameters
        ----------
        """
        if self.labelList:
            # return the label list
            return self.labelList
        else:
            return False
        
        
    def addLabel(self, label = None):
        """
        Add a label to the list of labels 
        Parameters
        ----------
        label : str
            The Label that will be added to the list of labels default (None)
        """
        
        # check if label is None
        if not label:
            return False
        # check if label is a String
        if not isinstance(label, str):
            return False
        # check if the input label is already in  the list
        elif label.lower() in self.labelList:
            return False
        # if checks are passed append label to the list
        else:
            self.labelList.append(label)
            return True
    
    def changeLabelPlace(self, label=None, newPlace=None):
        # check if the label is not None
        if not label:
            return False
        # check if the new place is passed
        elif not newPlace:
            return False
        # change label location in the list
        else:
            # remove the label
            self.labelList.remove(label)
            # insert the label to the neo location
            self.labelList.insert(newPlace, label)
            return True
        
    def setCurrentLabel(self, label=None, ID=None):
        # check if there is a label or an ID are provided
        if not (label or ID):
            return False
        # check if both a label and an ID are provided
        if label and ID:
            return False
        # if label is not None set current label
        if isinstance(label, str):
            # try to get the current label index
            try:
                self.currentLabelIndex = self.labelList.index(label.lower())
                return True
            # if the label is not found in the label list raise an exception
            except ValueError:
                print("This label is not in the labels list")
                return False
        elif isinstance(ID, int):
            # check if the id in the valid label list range
            if ID in range(len(self.labelList) + 1):
                self.currentLabelIndex = ID
                return True
            # throw exception if id is out of range
            else:
                raise Exception("ID is out of range")

        else:
            print("The input value is not valid if you want to set the current label by ID \
            please specify the ID by the keyword argument ID (eg : setCurrentLabel(ID = 3))")

    def getCurrentLabel(self):
        # check if the label stream is active
        if self.labelStreamerActive:
            # update the current label
            self.streamLabels(__startStream__=False)
        
        # return current selected label
        return self.labelList[self.currentLabelIndex]

    def streamLabels(self,timeInterval=5, reset=False, __startStream__=True):
        # check if the stream is being initialized
        if __startStream__:
            # set label list iterator to zero
            self.labelStreamIterator = 0
            # get length of the list that will be iterated
            self.labelBufferListLength = len(self.labelList)
            # check if the time interval is valid
            if timeInterval > 0:
                self.streamTimeInterval = timeInterval
            else:
                raise Exception("Time interval can not be less than or equal zero")
            # check if the label list is not empty
            if self.labelList:
                # activate the label stream
                self.labelStreamerActive = True
                # set the current label to the first label in the label list
                self.setCurrentLabel(ID=self.labelStreamIterator)
                self.streamerStartTime = time.time()
                return True
            else:
                raise Exception("No labels in the label list to stream")
        # check if the current label is the last in the list
        if self.labelStreamIterator == self.labelBufferListLength - 1:
            # deactivate the label stream
            self.labelStreamerActive = False
        
        # check if the stream is active
        if self.labelStreamerActive:
            # get current time
            self.streamerCurrentTime = time.time()
            # check if its time to update the current label
            if(self.streamerCurrentTime - self.streamerStartTime >= self.streamTimeInterval):
                # update the label iterator
                self.labelStreamIterator = self.labelStreamIterator+1
                # set current label to the new value
                self.setCurrentLabel(ID=self.labelStreamIterator)
                # update the start time
                self.streamerStartTime = time.time()
    
    def cancelStream(self):
        # deactivate the label stream
        self.labelStreamerActive = False

    def printLabels(self):
        print(self.labelList)