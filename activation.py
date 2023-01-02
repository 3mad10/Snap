import mouse
import time
from abc import ABC, abstractmethod
import keyboard

class Activator:
    """
    Class used for activating the sequence capturing
    """
    def __init__(self):
        self.active = False
    
    
    def getEvent(self):
        return self.event
    
    @abstractmethod
    def setEvent(self, event):
        """method to set an event for activation"""
    
    @abstractmethod
    def isActive(self):
        """Return True if an activation event is ongoing"""
    
    
    def waitUntilEvent(self):
        """
        Used to activate the sequence capture untill an event occurs
        eg : mouse pressed
        """
        self.active = True
        if(self.isActive()):
            self.active = False
        return self.active
    
    def waitForSeconds(self, seconds = 60):
        """
        Sequence capture active for given number of seconds
        """
        self.active = True
        if (not hasattr(Activator, 'start')) or (Activator.start == 0):  
            Activator.start =  time.time()
        if((time.time() - Activator.start) >= seconds):
            self.active = False
            Activator.start = 0
        return self.active
    
    def waitForMinutes(self, minutes = 1):
        """
        Sequence capture active for given number of minutes
        """
        self.active = True
        if (not hasattr(mouseActivator, 'start')) or (mouseActivator.start == 0):  
            mouseActivator.start =  time.time()
        if((time.time() - mouseActivator.start) >= (minutes * 60)):
            self.active = False
            mouseActivator.start = 0
        return self.active
    
    
class mouseActivator(Activator):
    """
    Class used for mouse activation events
    """
    def __init__(self, event = 'left'):
        if event not in ['left', 'right']:
            raise ValueError('The event have to be either left or right')
        self.event = event
        
    def setEvent(self, event):
        if event not in ['left', 'right']:
            raise ValueError('The event have to be either left or right')
        self.event = event
        
    def isActive(self):
        return mouse.is_pressed(button=self.event)
    
    
class keyboardActivator(Activator):
    """
    Class used for keyboard activation events
    """
    def __init__(self, event = 'space'):
        self.keys = ["q","w","e","r","t","y","u","i","o","p","a","s","d",
                     "f","g","h","j","k","l","z","x","c","v","b","n","m"," "]
        if event not in self.keys:
            raise ValueError(f"The {event} key is not supported please enter one of the following keys {self.keys}")
        self.event = event
        
    def isActive(self):
        return keyboard.is_pressed(self.event)
    
    def setEvent(self, event):
        if event not in self.keys:
            raise ValueError(f"The {event} key is not supported please enter one of the following keys {self.keys}")
        self.event = event