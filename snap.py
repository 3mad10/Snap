import numpy as np
from activation import mouseActivator
import pandas as pd
from labeling import Labeler
from matplotlib import pyplot as plt
from feature_extraction import MPExtractor
import cv2
import os


class Snap:
    def __init__(self, inputType='image',
                 activator=mouseActivator('left'),
                 outputIndicator=None,
                 featureExtractor=None,
                 labels='input',
                 labelList=None,
                 showData=False,
                 dataPath='./Data'):
        self.inputType = inputType
        self.activator = activator
        self.sequenceID = 0
        self.latestActiveState = False
        self.featureExtractor = MPExtractor(featureExtractor)
        self.dataset = np.array([])
        self.dataset_dataframe = None
        self.FullDataset = None
        self.addedElementsToTimeSeries = 2
        self.columnsList = None
        if labels == 'input':
            self.labeler = Labeler(labelList)
        if outputIndicator:
            self.outputIndicator = Indicator(outputIndicator)

    def addData(self, inputStream):
        self.inputStream = inputStream
        # Start stream
        while self.inputStream.isOpened():
            success, image = self.inputStream.read()
            image = cv2.flip(image, 1)
            self.imgShape = (image.shape[0], image.shape[1])
            if self.activator.isActive() and not self.latestActiveState:
                self.sequenceID = self.sequenceID + 1
            if not success:
                print("Ignoring empty camera frame.")
                continue
            if self.activator.isActive():
                self.addSample(image)
            self.latestActiveState = self.activator.isActive()
            cv2.imshow('MediaPipe Hands',image)
            if cv2.waitKey(5) & 0xFF == 27:
                break


        if not self.columnsList:
            self.columnsList = [str(i) for i in range(self.featureExtractor.getFeatureSize())] + ['Label','Sequence ID']
        self.dataset_dataframe = pd.DataFrame(self.dataset, columns=self.columnsList)
        inputStream.release()
        cv2.destroyAllWindows()

    def addSample(self, sample):
        sampleFeature = self.featureExtractor.extract(sample)
        sample = np.append(sampleFeature, [self.labeler.getCurrentLabel(), self.sequenceID])

        if sampleFeature is not None:
            if self.dataset.size == 0:
                self.dataset = np.reshape(sample,(1,self.featureExtractor.getFeatureSize() + self.addedElementsToTimeSeries))
            self.dataset = np.concatenate((self.dataset, 
                                           np.reshape(sample,(1,self.featureExtractor.getFeatureSize() + self.addedElementsToTimeSeries))), axis = 0)
        else:
            print("No sample feature")

    def loadData(self, path = 'Data', datasetName = 'out', featureList = None):
        if(os.path.exists(path+"/"+datasetName+".csv") and os.path.isfile(path+"/"+datasetName+".csv")):
            self.FullDataset = pd.read_csv(path+"/"+datasetName+".csv",index_col=0)
            return self.FullDataset
        else:
            return None

    def saveDataset(self, path = 'Data', datasetName = 'out', featureList = None):
        if featureList:
            if len(featureList) == self.dataset.shape[0] - 1:
                self.featureList = featureList
        else:
            self.featureList = [str(i) for i in range(self.dataset.shape[1] - 2)]

        columnsList = self.featureList + ['Label','Sequence ID']
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            self.dataset_dataframe.to_csv(path+"/"+datasetName+".csv")
        else:
            self.FullDataset = self.loadData(path = path, datasetName = datasetName, featureList = featureList)
            if self.FullDataset is not None:
                self.FullDataset = pd.concat([self.FullDataset, self.dataset_dataframe], axis = 0)
                self.FullDataset.reset_index(inplace=True, drop=True)
            else:
                self.FullDataset = self.dataset_dataframe
            self.FullDataset.to_csv(path+"/"+datasetName+".csv")

    def printDataset(self):
        print(self.dataset_dataframe)

    def plotData(self, sliceOfInterest = [24,25]):
        label_list = np.unique(self.dataset_dataframe.iloc[1:,-2])
        fig, ax = plt.subplots()
        #print(self.dataset.iloc[:,:-2])
        data = self.dataset_dataframe.iloc[:,:-2]

        dataOfInterest = data.iloc[:,sliceOfInterest]
        plt.xlim(0, 600)
        plt.ylim(0, 600)
        colorIdx = 0

        for index, row in dataOfInterest.iterrows():
            plt.plot([int(point) for idx, point in enumerate(row) if idx%2 == 0], 
                     [int(point) for idx, point in enumerate(row) if idx%2 != 0],'o' ,color = str(1/(2**(colorIdx/len(data)))))
            colorIdx+=1
        plt.gca().invert_yaxis()
        plt.show()
