'''
Created on 05.11.2011

@author: thomas
'''

import numpy as N
from math import ceil
from itertools import izip
from util import chkM,fftp,ifftp

try:
    # try to import cython version
    from _nsgtf_loop import nsgtf_loop
except ImportError:
    nsgtf_loop = None

if nsgtf_loop is None:
    from nsgtf_loop import nsgtf_loop

# what about theano?
try:
    import theano as T
except ImportError:
    T = None

try:
    import multiprocessing as MP
except ImportError:
    MP = None


#@profile
def nsgtf_sl(f_slices,g,wins,nn,M=None,real=False,reducedform=0,measurefft=False,multithreading=False):
    M = chkM(M,g)
    
    fft = fftp(measure=measurefft)
    ifft = ifftp(measure=measurefft)
    
    if real:
        assert 0 <= reducedform <= 2
        sl = slice(reducedform,len(g)//2+1-reducedform)
    else:
        sl = slice(0,None)
    
    maxLg = max(int(ceil(float(len(gii))/mii))*mii for mii,gii in izip(M[sl],g[sl]))
    temp0 = None
    
    if multithreading and MP is not None:
        mmap = MP.Pool().map
    else:
        mmap = map

    loopparams = []
    for mii,gii,win_range in izip(M[sl],g[sl],wins[sl]):
        Lg = len(gii)
        col = int(ceil(float(Lg)/mii))
        assert col*mii >= Lg
        gi1 = gii[:(Lg+1)//2]
        gi2 = gii[-(Lg//2):]
        p = (mii,gii,gi1,gi2,win_range,Lg,col)
        loopparams.append(p)

    # main loop over slices
    for f in f_slices:
        Ls = len(f)
        
        # some preparation    
        ft = fft(f)

        if temp0 is None:
            # pre-allocate buffer (delayed because of dtype)
            temp0 = N.empty(maxLg,dtype=ft.dtype)
        
        # A small amount of zero-padding might be needed (e.g. for scale frames)
        if nn > Ls:
            ft = N.concatenate((ft,N.zeros(nn-Ls,dtype=ft.dtype)))
        
        # The actual transform
        c = nsgtf_loop(loopparams,ft,temp0)
            
        # TODO: if matrixform, perform "2D" FFT along one axis
        # this could also be nicely parallalized
        yield mmap(ifft,c)  

        
# non-sliced version
def nsgtf(f,g,wins,nn,M=None,real=False,reducedform=0,measurefft=False,multithreading=False):
    return nsgtf_sl((f,),g,wins,nn,M=M,real=real,reducedform=reducedform,measurefft=measurefft,multithreading=multithreading).next()
