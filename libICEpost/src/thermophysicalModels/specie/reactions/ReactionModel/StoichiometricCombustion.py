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

import math
import sympy as sym

from .ReactionModel import ReactionModel
from ..Reaction.Reaction import Reaction
from libICEpost.src.thermophysicalModels.specie.specie.Mixture import Mixture, mixtureBlend
from libICEpost.src.thermophysicalModels.specie.specie.Molecule import Molecule

from libICEpost.Database import database

#############################################################################
#                               MAIN CLASSES                                #
#############################################################################
class StoichiometricCombustion(ReactionModel):
    """
    Reaction model of fuel combustion with infinitely fast chemistry. The
    system is modeled as two zones, reactants and products, separated by an
    infinitely thin reaction zone.
    
    NOTE:
    All fuels in the mixture must be contained in the 'fuel' entry, while the oxidizers
    in 'oxidizer'. By default the oxidizer is O2.
    
    TODO:
    Extend to handle a generic reaction set, where there might be more then one oxidizer
    
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Attributes:
        fuel:  list<Molecule>
            The oxidizing molecule
            
        oxidiser:  Molecule
            The oxidisers

        reactants:  (Mixture)
            The mixture of the reactants
        
        products:  (Mixture)
            The mixture of products of the reaction
            
        reactions:  (_Database)
           Database of oxidation reactions. Reference to database.chemistry.reactions
    
    """
    _ReactionType = "StoichiometricReaction"
    
    #########################################################################
    @property
    def fuel(self):
        """
        The sub-mixture of reactants with the fuels
        """
        self._updateFuels()
        return self.reactants.extract(self._fuels)
    
    ##############################
    @property
    def oxidizer(self):
        """
        The oxidizer
        """
        return self._oxidizer
    
    #########################################################################
    @classmethod
    def fromDictionary(cls, dictionary):
        """
        Args:
            dictionary (dict): The dictionary from which constructing
                {
                    "reactants" (Mixture): the mixture of reactants
                    "oxidiser" (Molecule): the oxidizer
                    "fuel" (list<Molecule>): the fuel molecuels in the mixture
                }
        
        Constructs from dictionary
        """
        try:
            entryList = ["reactants"]
            for entry in entryList:
                if not entry in dictionary:
                    raise ValueError(f"Mandatory entry '{entry}' not found in dictionary.")
            
            if not "oxidizer" in dictionary:
                dictionary["oxidizer"] = database.chemistry.specie.Molecules.O2
            
            out = cls\
                (
                    dictionary["reactants"],
                    dictionary["oxidizer"]
                )
            return out
            
        except BaseException as err:
            cls.fatalErrorInClass(cls.fromDictionary, "Failed construction from dictionary", err)
    
    #########################################################################
    #Properties:
    
    #########################################################################
    #Constructor:
    def __init__(self, reactants:Mixture, oxidizer:Molecule=database.chemistry.specie.Molecules.O2):
        """
        Args:
            reactants (Mixture): the mixture of reactants
            oxidizer (Molecule, optional): The oxidizing molecule. Defaults to database.chemistry.specie.Molecules.O2.
        """
        
        self.checkType(oxidizer, Molecule, "oxidizer")
        self._oxidizer = oxidizer
        
        super().__init__(reactants)
        

    #########################################################################
    #Operators:
    
    ################################
    
    #########################################################################
    #Methods:
    def _updateFuels(self):
        """
        Update list of fuels
        """
        fuels = []
        for s in self.reactants:
            if s["specie"].name in database.chemistry.specie.Fuels:
                fuels.append(s["specie"])
        self._fuels = fuels
        
        return self
        
    ###################################
    def _update(self, reactants=None):
        """
        Method to update the reactants based on the mixture composition (interface).
        """
        #Update reactants, return True if the reactants are already up-to-date:
        if super()._update(reactants):
            return True
        self._updateFuels()
        
        #Splitting the reactants into three steps:
        #1) Removing the non-reacting compounds
        #   ->  Identified as those not found in the reactants 
        #       of any reactions
        #2) Identification of the active reactions
        #   ->  Active reactions are those where all reactants are present
        #       in the mixture and at least one fuel and the oxidizer
        #3) Solve the balance
        
        #Look for the oxidation reactions for all fuels
        oxReactions = {}    #List of oxidation reactions
        for f in self._fuels:
            found = False
            for r in self.reactions[self.ReactionType]:
                react = self.reactions[self.ReactionType][r]
                if (f in react.reactants) and (self.oxidizer in react.reactants):
                    found = True
                    oxReactions[f.name] = react
                    break
            if not found:
                raise ValueError(f"Oxidation reaction not found in database 'rections.{self.ReactionType}' for the couple (fuel, oxidizer) = ({f.name, self.oxidizer.name})")
        
        #Identification of reacting compounds
        xReact = 0.0
        reactingMix = None
        activeReactions = []
        #Loop over specie of the reactants
        for specie in self.reactants:
            #Loop over all oxidation reactions to find the active reactions
            found = False
            for r in oxReactions:
                react = oxReactions[r]
                #Check if the specie in the reactants of the reaction
                if specie["specie"] in react.reactants:
                    #Check that all reactants of the reaction are found in the mixture,
                    #otherwise the reaction does not take place
                    active = True
                    for sR in react.reactants:
                        if not (sR["specie"] in self.reactants):
                            active = False
                            break
                    
                    if not self.oxidizer in react.reactants:
                        active = False
                    if not any([mol in react.reactants for mol in self._fuels]):
                        active = False
                    
                    #If not active, skip to next reaction
                    if not active:
                        continue
                    
                    #If here, an active reaction was found
                    found = True
                    
                    #Check if already added to reactions
                    if not react in activeReactions:
                        #Add to active reactions
                        activeReactions.append(react)
                    
            #add the specie to the reacting mixture if an active reaction was found
            if found:
                if reactingMix is None:
                    reactingMix = Mixture([specie["specie"]], [1])
                else:
                    reactingMix.dilute(specie["specie"], specie["X"]/(xReact + specie["X"]), "mole")
                xReact += specie["X"]
        
        #Removing inerts
        inerts = None
        xInert = 0.0
        for specie in self.reactants:
            if not specie["specie"] in reactingMix:
                if inerts is None:
                    inerts = Mixture([specie["specie"]], [1])
                else:
                    inerts.dilute(specie["specie"], specie["X"]/(xInert + specie["X"]), "mole")
                xInert += specie["X"]
        
        # print("Reactants:")
        # print(self.reactants)
        
        # print(f"Reacting mixture (X = {xReact})")
        # print(reactingMix)
        
        # print(f"Inerts (X = {xInert})")
        # print(inerts)
        
        #If no active reaction found, clone reactants to products:
        if reactingMix is None:
            self._products = self._reactants
            return self
        
        # print("Active reactions:",[str(r) for r in activeReactions])
        
        #To assess if lean or rich, mix the oxidation reactions based on the
        #fuel mole/mass fractions in the fuels-only mixture. If the concentration
        #of oxigen is higher then the actual, the mixture is rich, else lean.
        
        
        #Get stoichiometric combustion products:
        #   -> Solving linear sistem of equations 
        #
        #   R0: c1*[f00*F0 + o0*Ox   ]          | Oxidation reaction fuel F0 (reactants)
        #   R1: c2*[f11*F1 + o1*Ox   ]          | Oxidation reaction fuel F1 (reactants)
        #   R2: c3*[f22*F2 + o2*Ox   ]          | Oxidation reaction fuel F2 (reactants)
        #   ----------------------------------
        #   Rtot: f(f1*F1 + f2*F2 + ...) + o*Ox | Overall reactants
        #
        #   Where (f1, f2, ...) is the composition of the fuel-only mixture (known)
        #   and (c1, c2, ..., f) are the unknowns
        #
        #   The equations are:
        #   sum(c_i * f_ii) = f*f_i for i in (1,...,n_fuels)
        #   sum(c_i) = 1 for i in (1,...,n_fuels)
        #
        #   Hence n_fuels+1 unknowns and n_fuel+1 equations
        #
        #   |f00  0   0  ... -f0| |c1| |0|
        #   | 0  f11  0  ... -f1|*|c2|=|0|
        #   |...                | |..| |.|
        #   | 1   1   1  ...  0 | |f | |1|
        #
        #   [M]*x = v
        #
        
        fuelMix = self.fuel
        
        M = self.np.diag([oxReactions[f.name].reactants[f.name]["X"] for f in self._fuels])
        M = self.np.c_[M, [-fuelMix[f]["X"] for f in self._fuels]]
        M = self.np.c_[M.T, [1.]*(len(fuelMix)) + [0.]].T
        v = self.np.c_[self.np.zeros((1,len(fuelMix))), [1]].T
        xStoich = self.np.linalg.solve(M,v).T[0][:-1]
        
        # print(xStoich)
        
        stoichReactingMix = mixtureBlend\
            (
                [oxReactions[f.name].reactants for f in self._fuels], 
                [xx for xx in xStoich],
                "mole"
            )
        
        # print("Fuel mixture:")
        # print(fuelMix)
        
        # print("Stoichiometric reacting mixture:")
        # print(stoichReactingMix)
        
        prods = mixtureBlend\
            (
                [oxReactions[f.name].products for f in self._fuels], 
                [xx for xx in xStoich],
                "mole"
            )
        
        # print("Stoichiometric products:")
        # print(prods)
        
        #If the reaction is not stoichiometric, add the non-reacting part:
        if not math.isclose(stoichReactingMix[self.oxidizer]["X"],reactingMix[self.oxidizer]["X"]):
            if (reactingMix[self.oxidizer]["X"] > stoichReactingMix[self.oxidizer]["X"]):
                #Get the mole fraction of excess oxidizer
                xExc = reactingMix[self.oxidizer]["X"] - stoichReactingMix[self.oxidizer]["X"]
                excMix = Mixture([self.oxidizer],[1.])
            else:
                xExc = stoichReactingMix[self.oxidizer]["X"] - reactingMix[self.oxidizer]["X"]
                excMix = self.fuel
            #Add non-reacting compound
            prods.dilute(excMix,xExc, "mole")
            
            # print(f"Excess mixture: (X = {xExc})")
            # print(excMix)
        
        #Add inherts:
        if not inerts is None:
            prods.dilute(inerts, xInert, "mole")
        
        self._products = prods
        
        # print("Products:")
        # print(prods)
        
        #Has updated
        return False
        
    ################################
    
    
#########################################################################
#Add to selection table
ReactionModel.addToRuntimeSelectionTable(StoichiometricCombustion)
