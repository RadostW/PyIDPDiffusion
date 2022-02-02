import numpy as np

def get_spherical():
    vec = np.random.randn(3)
    return vec/np.sqrt(np.sum(vec**2))

def _get_chain_recursive(begin,end,sizes):
    #print((begin,end,sizes))
    """
    Get chain starting with bead of size sizes[begin] and ending with bead sizes[end-1]
    """
    
    if begin == end:
        return np.array([[]])
    elif begin == end-1:
        return np.array([[0,0,0]])
    else:
        margin = 0.001 # allow 0.1% intersections
        
        intersecting = True
        while intersecting:
            midpoint = (begin+end)//2
            left_chain = _get_chain_recursive(begin,midpoint,sizes)
            right_chain = _get_chain_recursive(midpoint,end,sizes)
            
            chain_offset = (sizes[midpoint] + sizes[midpoint-1])*get_spherical()
                        
            right_chain_shifted = right_chain + chain_offset
            
            squared_distances = np.sum((left_chain[:,np.newaxis] - right_chain_shifted[np.newaxis,:])**2, axis = -1)
            
            left_sizes = sizes[begin:midpoint]
            right_sizes = sizes[midpoint:end]
            
            shortcuts =  (1-margin)*(left_sizes[:,np.newaxis]+right_sizes[np.newaxis,:])**2 - squared_distances
            if np.all(shortcuts < 0):
                return np.vstack([left_chain,right_chain_shifted])
            else:
                #print(end-begin)
                intersecting = True

def get_chain(sizes):
    return _get_chain_recursive(0,len(sizes),sizes)

def get_chains(sizes,n):
    return np.array([get_chain(sizes) for x in range(n)])
                
if __name__ == "__main__":
    print(get_chains(np.ones(17),1))
            
