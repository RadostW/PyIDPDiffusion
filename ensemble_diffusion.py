import numpy as np
import pygrpy

def rh(ensemble,sizes):
    grand_grand_mu = np.array([pygrpy.grpy_tensors.muTT(locations,sizes) for locations in ensemble])
    grand_mu = np.mean( grand_grand_mu , axis = 0 )    
    grand_trace = np.trace(grand_mu,axis1=-2,axis2=-1)
    
    inv_mat = np.linalg.inv(grand_trace)
    total = np.sum(inv_mat)
    return total / (2*np.pi)
    
    
if __name__ == "__main__":
    ensemble = np.array([[[0,0,0],[0,0,2]]])
    sizes = np.array([1,1])
    rh(ensemble,sizes)
