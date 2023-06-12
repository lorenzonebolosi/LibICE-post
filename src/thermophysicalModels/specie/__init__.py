"""
@author: F. Ramognino       <federico.ramognino@polimi.it>
Last update:        12/06/2023

Package for handling chemistry and thermodynamic properties of gasseous mixtures.

Content of the package:
    specie (package)
        Classes for describing:
            -> Atomic specie
            -> Molecules
            -> Mixtures
        
    thermo (package)
        Classes and packages for handling thermodynamic properties, reactions, thermodynamic/reaction models, etc.
"""

from Database import database
database["chemistry"] = {}
