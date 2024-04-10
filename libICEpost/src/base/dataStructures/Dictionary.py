#####################################################################
#                                 DOC                               #
#####################################################################

"""
@author: F. Ramognino       <federico.ramognino@polimi.it>
Last update:        12/06/2023
"""

#####################################################################
#                               IMPORT                              #
#####################################################################

from ..Utilities import Utilities
from collections import OrderedDict

#############################################################################
#                               MAIN CLASSES                                #
#############################################################################

class Dictionary(OrderedDict, Utilities):
    """
    Ordered dictionary embedding some useful OpenFOAM-like methods.
    """
    
    #############################################################################
    def __init__(self, *args,**argv):
        """
        Same constructor as collections.OrderedDict class.
        """
        try:
            OrderedDict.__init__(self,*args,**argv)
            
        except BaseException as err:
            self.fatalErrorInClass(self.__init__,f"Construction of {self.__class__.__name__} entry failed", err)
    
    #############################################################################
    @classmethod
    def fromFile(cls, fileName):
        """
        fileName:   str
            Path of the file
        Read the variables stored in a python file (Runs the code in the file and retrieves the local variables)
        """
        try:
            cls.checkType(fileName, str, "fileName")
        except BaseException as err:
            cls.fatalErrorInClass(cls.fromFile,f"Argument checking failed", err)
            
        try:
            outDict = cls.__init__()
            
            loc = locals().copy()
            oldLoc = list(loc)
            
            exec(open(self.fileName).read())
            
            loc = locals().copy()
            for l in loc.keys():
                if not l in (oldLoc + ["oldLoc", "loc"]) and (not isinstance(loc[l], ModuleType)):
                    outDict[l] = loc[l]
            
        except BaseException as err:
            cls.fatalErrorInClass(cls.fromFile,f"Error reading {cls.__name__} from file {fileName}", err)
        
        return outDict
        
    #############################################################################
    def lookup(self, entryName):
        """
        entryName:  str
            Name of the entry to look for
        
        Same as __getitem__ but embeds error handling
        """
        try:
            self.checkType(entryName, str, "entryName")
        except BaseException as err:
            self.fatalErrorInClass(self.lookup,f"Argument checking failed", err)
            
        if not entryName in self:
            self.fatalErrorInClass(self.lookup, f"Entry '{entryName}' not found in Dictionary. Available entries are:\n\t" + "\n\t".join([str(k) for k in self.keys()]))
        else:
            return self[entryName]
    
    ######################################
    def lookupOrDefault(entryName, default, fatal=True):
        """
        entryName:  str
            Name of the entry to look for
        default:    instance
            Instance to return in case the value is not found. It is also used for typeChecking
        fatal:      bool (True)
            If the type is not consistent rise a FatalError
            
        Lookup of give a default value if not found
        """
        try:
            cls.checkType(entryName, str, "entryName")
            cls.checkType(fatal, bool, "fatal")
        except BaseException as err:
            self.fatalErrorInClass(self.lookupOrDefault,f"Argument checking failed", err)
            
        if not entryName in self:
            self.fatalErrorInClass(self.lookupOrDefault, f"Entry '{entryName}' not found in Dictionary. Available entries are:\n\t" + "\n\t".join([str(k) for k in self.keys()]))
        else:
            return self[entryName]
    
    ######################################
    def _correctSubdicts(self):
        """
        Convert ricorsively every subdictionary into Dictionary classes.
        """
        try:
            for entry in self:
                if isinstance(self[entry], dict) and not isinstance(self[entry], Dictionary):
                    self[entry] = Dictionary(**self[entry])
            return self
        except BaseException as err:
            self.fatalErrorInClass(self._correctSubdicts,f"Error updating subdictionary types", err)
    
    
    ######################################
    def __setitem__(self, *args, **argv):
        try:
            super(self,self).__setitem__(*args, **argv)
            self._correctSubdicts()
            return self
        except BaseException as err:
            self.fatalErrorInClass(self.__setitem__,f"Error setting Dictionary item", err)
    
    ######################################
    def update(self, **kwargs):
        """
        kwargs:    dict
            Keyword-argumentrs to be updated in dictionary
            
        Performs like dict.update() method but recursively updates sub-dictionaries
        """
        try:
            cls.checkType(Dict, dict, "Dict")
        except BaseException as err:
            self.fatalErrorInClass(self.update,f"Argument checking failed", err)
        
        try:
            for key in kwargs:
                if (isinstance(kwargs[key],dict)) and (key in self):
                    self[key].update(**kwargs[key])
                else:
                    super(self,self).update({key:kwargs[key]})
                    
            self._correctSubdicts()
        except BaseException as err:
            self.fatalErrorInClass(self.update,f"Error updating dictionary keys", err)
        
        return self
