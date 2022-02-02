import re
import numpy as np

aminoacidMasses = {
"A":7.108e1,
"C":1.0314e2,
"D":1.1509e2,
"E":1.2912e2,
"F":1.4718e2,
"G":5.706e1,
"H":1.3715e2,
"I":1.1317e2,
"K":1.2818e2,
"L":1.1317e2,
"M":1.3121e2,
"N":1.1411e2,
"P":9.712e1,
"Q":1.2841e2,
"R":1.562e2,
"S":8.708e1,
"T":1.0111e2,
"V":9.914e1,
"W":1.8621e2,
"Y":1.6318e2,

"*":0.0,
"Z":0.0,
"O":0.0,
"U":0.0,
"J":0.0,
"X":0.0,
"B":0.0,
}

def parse(text):
    legal_chars = ''.join(re.findall(r'[A-Z[\]]',text))
    chunks = re.finditer(r'[\[]?[A-Z][A-Z]*[\]]?',legal_chars)
    beads = []
    total_mass = 0
    for chunk in chunks:
        if ']' in chunk[0] or '[' in chunk[0]: #structured region
            region_mass = 0
            for char in chunk[0]:
                if char in aminoacidMasses.keys():
                    region_mass += aminoacidMasses[char]
                    total_mass += aminoacidMasses[char]
            beads += [(0.7525*np.cbrt(region_mass),0.7525*np.cbrt(region_mass),2)]
        else:
            for char in chunk[0]:
                beads += [(1.9025,4.2,1)]
                total_mass += aminoacidMasses[char]
                
    return {
    "bead_steric_sizes" : np.array([b[0] for b in beads]),
    "bead_hydrodynamic_sizes" : np.array([b[1] for b in beads]),
    "bead_types" : np.array([b[-1] for b in beads]),
    "total_mass" : total_mass
    }

