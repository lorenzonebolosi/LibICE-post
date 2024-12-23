# -*- coding: utf-8 -*-
"""
Testing solver for post-processing of CFD results from spark-ignition simulations
"""

#Importing
import os
import traceback
from libICEpost.src.engineModel.EngineModel.EngineModel import EngineModel
from libICEpost.src.base.dataStructures.Dictionary import Dictionary

#Define function for simpify loading:
def loadModel(path:str, controlDictName:str="controlDict.py") -> EngineModel|None:
    """
    Convenient function for loading the engineModel from the constrolDict.py file at specific 'path'.

    Args:
        path (str): The path where to find the controlDict.py file

    Returns:
        EngineModel: The engine model.
    """
    
    try:
        # Load the constrol dictionary
        print(f"Loading engine model from {path}/{controlDictName}")
        controlDict = Dictionary.fromFile(f"{path}/{controlDictName}")
        
        # Lookup engine model type and its dictionary
        engineModelType:str = controlDict.lookup("engineModelType")
        engineModelDict:Dictionary = controlDict.lookup(engineModelType + "Dict")
        
        #Construct from run-time selector
        model:EngineModel = EngineModel.selector(engineModelType, engineModelDict)
        return model
    
    except BaseException as err:
        print(f"Failed loading model from {path}:\n\t{err}")
        print(traceback.format_exc())
    

#Getting the current path (needed when running in debug mode)
thisPath, _ = os.path.split(__file__)
print(f"thisPath = {thisPath}")
os.chdir(thisPath)  #Move here if in debug

#Load the model
model = loadModel("./dictionaries/")

#Process the data in the engine model
model.process()

############################################################
# Combined plot of pressure trace and rate of heat release #
############################################################
#Importing matplotlib and pyplot
from matplotlib import pyplot as plt

#Setting plotting parameters
plt.rcParams.update({
    # "text.usetex": True,
    # "font.family": "serif",
    "font.monospace": ["Times"],
    "xtick.labelsize":22,
    "ytick.labelsize":22,
    'axes.labelsize': 28,
    'axes.titlesize': 24,
    "legend.fontsize":20,
    'lines.linewidth': 3,
    'axes.linewidth': 2,
    'figure.figsize':(6,6),
    # 'figure.dpi':10
})
#Plotting pressure-ROHR
axP, axRohr = model.plotP_ROHR(label="CFD", legend=True, c="k", figsize=(6,8))

#Adjust axes, limits, legend
plt.tight_layout()
axP.set_xlim((-30,30))  #x axis
axP.set_ylim((-10,40))  #pressure
axRohr.set_ylim((0,100)) #ROHR
axP.legend(loc="upper left")

#Plotting p-V diagram
ax = model.plotPV(label="CFD", timingsParams={"markersize":120, "linewidth":2})

#Show the figures
plt.show()