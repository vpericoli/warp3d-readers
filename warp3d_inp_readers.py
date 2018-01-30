"""
Vincente Pericoli
UC Davis

reader to get info about warp3d input files.
quite dirty and inefficient, but gets the job done.
"""

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# imports
#
import numpy
from reverse_readline import reverse_readline

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# superclass with helper routines
#
class WarpInputFile(object):
    """ WARP3D input file object """
    
    def __init__(self, filename=None, inptype=None):
        
        # assign inputs
        self.filename = filename
        self.inptype  = inptype
        # check input file type
        self.__chk_valid_inptype()
        
    def __chk_valid_inptype(self):
        valid_types = ("incid","coord","main","combined")
        if( self.inptype is None ):
            return
        for vt in valid_types:
            if( vt in self.inptype ):
                return
        raise Exception("Invalid input file-type.")
        return
    
    def __skip_line(self, line):
        """ checks if the line should be skipped over (e.g. if it's a comment line) """
        # skip line if...
        if( "echo" in line ):
            return True 
        if( line[0:2] == "c "):
            # comment character
            return True
        if( line[0:2] == "! "):
            # comment character
            return True
        # otherwise
        return False
        
    def read_incid(self):
        """ read element incidences """
        #
        # obtain size of problem
        #
        if( "incid" in self.inptype ):
            for line in reverse_readline(self.filename):
                if( line[0] == " " ):
                    L = line.strip().split()
                    nele = int(L[0])
                    nnpe = len(L) - 1
                    break
                    
        elif( "main" in self.inptype ):
            raise NotImplementedError("Not implemented for inptype main")
            
        elif( "combined" in self.inptype ):
            with open(self.filename,"r") as fObj:
                readbool = False
                for line in fObj:
                    # seek to incidences keyword
                    if( "incid" in line ):
                        readbool = True
                    if( self.__skip_line(line) ):
                        continue
                    if( not readbool ):
                        continue
                        
                    # check for end of incidences keyword
                    if( (line.strip() == "") or ("coord" in line) ):
                        break
                    
                    # otherwise, keep track of the last line
                    last_line = line
                    
            # use last line of incid to set size
            L = last_line.strip().split()
            nele = int(L[0])
            nnpe = len(L) - 1
                        
        else:
            raise Exception("bad")
        
        #
        # read in the incidences
        #
        
        # preallocate
        incid = numpy.zeros((nele,nnpe),dtype=numpy.int_)
        
        with open(self.filename,"r") as fObj:
            readbool = False
            for line in fObj:
                # seek to  'incidences' keyword
                if( "incid" in line ):
                    readbool = True
                    continue
                if( self.__skip_line(line) ):
                    continue
                if( not readbool ):
                    continue
    
                # check for end of incidences keyword
                if( (line.strip() == "") or ("coord" in line) ):
                    break
                
                # read in data
                L = line.strip().split()
                A = numpy.asarray(L,dtype=numpy.int_)
                incid[A[0]-1,:] = A[1:]
        
        if( not readbool ):
            raise Exception("nothing read")
    
        self.incid = incid
        return
        
        
    def read_coord(self):
        """ read nodal coords """
        #
        # obtain size of problem
        #
        if( "coord" in self.inptype ):
            # just read file in reverse
            for line in reverse_readline(self.filename):
                if( line[0] == " " ):
                    L = line.strip().split()
                    nnod = int(L[0])
                    break
                    
        elif( "main" in self.inptype ):
            raise NotImplementedError("Not implemented for inptype main")
            
        elif( "combined" in self.inptype ):
            # open file, read to end of coords
            with open(self.filename,"r") as fObj:
                readbool = False
                for line in fObj:
                    # seek to coords keyword
                    if( "coord" in line ):
                        readbool = True
                    if( self.__skip_line(line) ):
                        continue
                    if( not readbool ):
                        continue
                        
                    # check for end of coords keyword
                    if( (line.strip() == "") or ("incid" in line) ):
                        break
                    # otherwise, keep track of the last line
                    last_line = line
                    
            # use last line of coords to set size
            L = last_line.strip().split()
            nnod = int(L[0])
            
        else:
            raise Exception("bad")
        
        #
        # read in the coords
        #
        
        # preallocate
        coord = numpy.zeros((nnod,3),dtype=numpy.float64)
        
        with open(self.filename,"r") as fObj:
            readbool = False
            for line in fObj:
                # seek to  'coordinates' keyword
                if( "coord" in line ):
                    readbool = True
                    continue
                if( self.__skip_line(line) ):
                    continue
                if( not readbool ):
                    continue
    
                # check for end of coords keyword
                if( (line.strip() == "") or ("incid" in line) ):
                    break
                
                # read in data
                L = line.strip().split()
                A = numpy.asarray(L[1:],dtype=numpy.float64)
                N = numpy.int64(L[0])
                coord[N-1,:] = A[:]
                
        if( not readbool ):
            raise Exception("nothing read")
            
        self.coord = coord
        return
    
    def read_coords(self):
        # equate names
        self.read_coord()
        return
        
