"""
Vincente Pericoli
UC Davis

Read translated binary packet data, originating from 
my modified packet reader program. The files to read
are a hybrid comma-separated form.

THIS WILL LIKELY ONLY WORK FOR THE COHESIVE ELEMENT OUTPUTS

This is quick and dirty.
"""

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# imports
#
import os, numpy, scipy.io
from reverse_readline import *

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# class
#
class warpBinaryTranslatedOutput(object):

    #
    # init
    #
    def __init__(self, read_file):
        
        # initialize self storage variables
        self.data      = None
        self.nsteps    = None
        self.ndatacols = None
        self.nelems    = None
        self.elem_list = None
        self.nintpts   = None
        self.eindex    = None
        
        # set read file
        self.read_file = read_file
        
        # get problem size info
        self.getNumSteps()
        self.getNumDataCols()
        self.getNumElemsPoints()
        self.buildElemIndex()
        
        # obtain data array
        self.getOutput()
        return
    
    #
    # helper routines
    #
    def getNumSteps(self):
        """ get number of steps. should in last line of file """
        # read last line, split, convert step string to int
        for line in reverse_readline(self.read_file):
            nsteps = int( line.strip().split(",")[0] )
            break
        self.nsteps = nsteps
        return
    
    def getNumDataCols(self):
        """ get number of data columns """
        with open(self.read_file,'rb') as fObj:
            # find "nvalues" string, split, convert to int
            for line in fObj:
                if "nvalues:" in line:
                    ndc = int( line.split("nvalues:")[-1] )
                    break
        self.ndatacols = ndc
        return
        
    def getNumElemsPoints(self):
        """ get number of elements and number of int points """
        with open(self.read_file,'rb') as fObj:
            # read thru first step, counting all elems.
            # quite inefficient...
            elem_list  = []
            num_points = 0
            for line in fObj:
                # skip comment lines and blank lines
                if (not line.rstrip()) or ("#" in line[0:3]):
                    continue
                # otherwise read line and get data
                line  = line.strip().split(",")
                step  = int(line[0])
                elem  = int(line[1])
                point = int(line[2])
                # if step 2, we've reached the end.
                if step > 1:
                    break
                assert(step == 1) # sanity check
                # otherwise, update info
                if elem not in elem_list:
                    elem_list.append(elem)
                if point > num_points:
                    num_points = point
        
        # save to self and return
        self.nelems    = len(elem_list)
        self.elem_list = tuple(elem_list)
        self.nintpts   = num_points
        return

    def buildElemIndex(self):
        """ build an element index """
        eindex = {}
        for i,elem in enumerate(self.elem_list):
            eindex[elem] = i
        self.eindex = eindex
        return

    #
    # routines to read data
    # 
    def getOutput(self):
        """ 
        get the output data 
        
        data is accessed like so:
        data[step,elem_index,ip,values]
        
        the elem_index may be retrieved by using eindex[elem]
        """
        
        # rename for convenience
        nsteps = self.nsteps
        ncols  = self.ndatacols
        numel  = self.nelems
        nips   = self.nintpts
        
        # preallocate
        data = numpy.zeros([nsteps,ncols,numel,nips],dtype=numpy.float64)
        
        # fetch data
        with open(self.read_file,'rb') as fObj:
            for line in fObj:
                # skip comment lines and blank lines
                if (not line.rstrip()) or ("#" in line[0:3]):
                    continue
                # otherwise, read in data
                line  = line.strip().split(",")
                step  = int(line[0])
                elem  = int(line[1])
                point = int(line[2])
                # set indices (for readability)
                si = step - 1
                ei = self.eindex[elem]
                pi = point - 1
                # assign data to array
                data[si,:,ei,pi] = numpy.float64(line[3:3+ncols])
        
        # save to self and return
        self.data = data
        return
        
    #
    # routines to write data
    #
    def writeMAT(self, write_file):
        """ write data array to .MAT database """
        scipy.io.savemat(write_file, self.__dict__, appendmat=False)
        return
    
    def saveMAT(self, write_file):
        """ same as writeMAT """
        self.writeMAT(write_file)
        return