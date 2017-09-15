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
import os, numpy, scipy.io, subprocess
from reverse_readline import *

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# classes
#
class warpBinaryPacketFile(object):
    def __init__(self, packetfile="binary_packets.out"):
        self.packetfile = packetfile
        return
    
    @property
    def packet_reader(self):
        return "C:\\warp3d-vpdev\\warp3d-vpdev\\packet_dir\\my_packet_reader.exe"
    
    def __str_space_assemble(self,items):
        s = ""
        for item in items:
            s += " " + str(item)
        return s
    
    def translate_CZM(self):
        self.translate(packetno=31,transfile="czm_tractions.out")
        self.translate(packetno=32,transfile="czm_displacements.out")
        return
        
    def translate(self, packetno, transfile):
        # check args
        if not (type(packetno) == int):
            raise TypeError("packetno must be an integer")
        if not (type(transfile) in (str,unicode)):
            raise TypeError("transfile must be a string")
        if len(transfile) > 80:
            raise RuntimeError("transfile name is too long (invalid)")
        # assemble and execute
        args = [packetno, self.packetfile, transfile]
        args = self.__str_space_assemble(args)
        subprocess.check_call(self.packet_reader + args, shell=True)
        return
    

class warpBinaryTranslatedOutput(object):

    #
    # init
    #
    def __init__(self, read_file=None, czm_data=None):
        
        # check args
        if (czm_data is None) and (read_file is None):
            raise TypeError("read_file and czm_data are both None.")
        elif (czm_data is not None) and (read_file is not None):
            raise TypeError("both read_file and czm_data cannot be set independently.")
            
        # assign default CZM stuff
        if czm_data is None:
            col_names = None
        elif czm_data in "tractions":
            read_file = "czm_tractions.out" # hard coded in warpBinaryPacketFile()
            col_names = "[shear1, shear2, eff. shear, normal, gamma, gamma_ur]"
        elif czm_data in "displcaments":
            read_file = "czm_displacements.out" # hard coded in warpBinaryPacketFile()
            col_names = "[shear1, shear2, shear, normal]"
        
        # set read file, col_names
        self.read_file = read_file
        self.col_names = col_names
        
        # initialize self storage variables
        self.data      = None
        self.nsteps    = None
        self.ndatacols = None
        self.nelems    = None
        self.elem_list = None
        self.nintpts   = None
        self.eindex    = None
        
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
        
        # preallocate; set "access info" for user
        data = numpy.zeros([nsteps,ncols,numel,nips],dtype=numpy.float64)
        self.access = "[step, col, elem, int.pt.]"
        
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