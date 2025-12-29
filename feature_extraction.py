import mediapipe as mp
import numpy as np
from abc import abstractmethod
import cv2


class BaseExtractor:
    """ Class for extracting features of the input frame """
    def __init__(self, extractor = 'hand', features_size = 0, feature_dimensions = 1):
        self.extractor = extractor
        self.features_size = features_size
        self.feature_dimensions = feature_dimensions

    @abstractmethod
    def extract(self, inputData):
        """
        Extract the features from the input data, the implementation depends on the features to be extracted
        
        Parameters
        ----------
        inputData : any
            The input data shall be of any type

        Return
        ----------
        arr : return an array of shape (1,features_size)
        """
    
    def getFeatureSize(self):
        """
        Get the feature size of the data (number of features to be extracted)
        
        Parameters
        ----------

        Return
        ----------
        features_size
        """
        return self.features_size

    def setFeatureSize(self, feature_size = 0):
        """
        Set the feature size of the data (number of features to be extracted)

        Parameters
        ----------
        feature_size : int indicating the number of features that will be extracted if not set
        the feature_size shall be evaluated from the input data as features.shape[0]

        Return
        ----------
        None
        """
        if feature_size>0:
            self.features_size = feature_size
        else:
            raise ValueError("Feature size can not be less than or equal to zero")


class MPExtractor(BaseExtractor):
    """ Class for extracting features of the input frame based on Media pipe models """
    def __init__(self, extractor = 'hand', features_size = 0, feature_dimensions = 1):
        """
        Initialize mediapipe extractor
        """
        # Initialize base class
        super().__init__(extractor, features_size, feature_dimensions)
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_hands  = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_hands  = mp.solutions.hands
        self.hands = mp_hands.Hands(model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def extract(self, inputData):
        inputData.flags.writeable = False
        inputData = cv2.cvtColor(inputData, cv2.COLOR_BGR2RGB)
        # Get the feature from mediapipe model
        results = self.hands.process(inputData)
        inputData.flags.writeable = True
        inputData = cv2.cvtColor(inputData, cv2.COLOR_RGB2BGR)
        # Check if there are features extracted from the input data
        if results.multi_hand_landmarks:
            # Initialize an array to hold the features extracted
            features = np.array([])
            # Loop over the results and 
            for hand_landmarks in results.multi_hand_landmarks:
                for id, lm in enumerate(hand_landmarks.landmark):
                    if lm.x and lm.y:
                        # Check if the features array is still empty
                        if features.size == 0:
                            # if the features array is empty assign the features array to the first value extracted
                            # multiply by te input data to scale from 0->1 to input width * height withoout normalization
                            features = np.array([int(lm.x*inputData.shape[1]), int(lm.y*inputData.shape[0])])
                        # If the features array already contains value/s
                        else:
                            # Stack the features array with the added value
                            features = np.hstack((features, np.array([int(lm.x*inputData.shape[1]), int(lm.y*inputData.shape[0])])))

            # If the feature size was not assigned by the user assign it to features.shape[0]
            if not self.features_size:
                self.features_size = features.shape[0]
            # Reshape the features to self.feature_dimensions * self.features_size
            try:
                features = np.reshape(features, (self.feature_dimensions, self.features_size))
            except ValueError:
                return None

            return features