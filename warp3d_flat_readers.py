"""
Vincente Pericoli
UC Davis

reader to get output from warp3d files.    
quick and dirty

to-do: 
    * add ability to request multiple columns
      of data, e.g. request displacement in 
      both the x and y directions. Currently
      you have to re-read the output file...
      very inefficient.
"""

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# imports
#
import os, fnmatch, numpy

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# superclass with helper routines
#
class warpFlatOutputHelpers(object):
    #
    # init
    #
    def __init__(self):
        """ empty init """
        return
    
    #
    # properties
    #
    @property
    def output_dir(self):
        return self._output_dir
    @output_dir.setter
    def output_dir(self,s):
        if not os.path.isdir(s):
            raise RuntimeError("Invalid directory!")
        self._output_dir = s
        return 
        
    @property
    def output_type(self):
        return self._output_type
    @output_type.setter
    def output_type(self, type):
        self._output_type = type.lower()
        return
        
    @property
    def obj_nums(self):
        return self._obj_nums
    @obj_nums.setter
    def obj_nums(self, obj_nums):
        if not hasattr(obj_nums,'__iter__'):
            obj_nums = (obj_nums,)
        self._obj_nums = obj_nums
        self.nobjs = len(obj_nums)
        return
        
    @property
    def writeNumTemplate(self):
        return "{:>13.6e}"
    
    #
    # helper functions
    #
    def _getNumSteps(self, dirpath):
        """ obtain the number of steps """
        outid  = self._outputFilenameIdentifier()
        outfmt = self.outputFormatType()
        nfout = len(fnmatch.filter(os.listdir(dirpath), outid + '*_' + outfmt))
        if (nfout == 0):
            raise RuntimeError("no output found")
        return num_steps
    
    def _getNumNodesElems(self, filepath):
        """ given input file or woutput, obtain number of nodes and elements """
        with open(filepath,'rb') as fObj:
            for line in fObj:
                if( ("number of" in line) 
                     and ("elements" in line) 
                     and ("nodes" in line) ):
                     # this line contains node and element numbers
                     linesplit = line.strip().split(" ")
                     numel = int( linesplit[linesplit.index("elements")+1] )
                     nnod  = int( linesplit[linesplit.index("nodes")+1] )
                     self.tot_num_elems = numel
                     self.tot_num_nodes = nnod
                     return
    
    def _composeCSVString(self, iterable_of_strings):
        """ iterable of strings converted to CSV write string """
        write_string = ""
        for s in iterable_of_strings:
            write_string += s
            write_string += ", "
        write_string += "\n"
        return write_string
    
    def _outputFilenameTemplate(self):
        """ filename format template """
        fmt = self.outputFormatType()
        template_dict = {"reaction"       : "wnr{:05d}_" + fmt,
                         "displacement"   : "wnd{:05d}_" + fmt,
                         "cohesive_state" : "wem{:05d}_" + fmt + "_cohesive"}
        if not (self.output_type in template_dict.keys()):
            raise RuntimeError("Invalid output_type")
        return template_dict[self.output_type]
        
    def _outputFilenameIdentifier(self):
        """ obtain the output identifiers (prefix) """
        return self._outputFilenameTemplate()[0:3]

    def sumOutput(self):
        """ implicitly assumed that we want to sum objects accross step """
        self.output = self.output.sum(axis=1,keepdims=True)
        return
        
    def writeCSVOutput(self, filename, header, array):
        # need headers, iterable of arrays, step numbers
        # arrays are populated. write to CSV
        nsteps = array.shape[0]
        ncols  = array.shape[1]
        write_num_template = self.writeNumTemplate
        
        with open(filename,"wb") as fObj:
            # write header
            fObj.write(header)        
            # write data
            for s in range(1,nsteps+1):
                # i = row index
                i = s - 1
                
                # make strings
                strlist = []
                for c in range(0,ncols):
                    strlist.append(write_num_template.format(array[i,c]))
                write_string = composeWriteString(strlist)
                
                # write
                fObj.write(write_string)
        return
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# flat file reader
#
class warpTextOutput(warpFlatOutputHelpers):
    #
    # init
    #
    def __init__(self, output_dir, output_type, obj_nums, data_cols):
        # get templates, allocate numpy arrays, 
        
        self.output_dir  = output_dir
        self.output_type = output_type
        self.obj_nums    = obj_nums
        self.data_index  = data_col - 1
        
        # initialize
        self.nsteps = self._getNumSteps(self.output_dir)
        self.stepfile_template = self._outputFilenameTemplate()
        
        # preallocate
        self.output = numpy.zeros([self.nsteps,self.nobjs], dtype=numpy.float64)
        
        # execute
        self.getOutput()
        return
    #
    # props
    #
    @property
    def outputFormatType(self):
        """ define output format type """
        return "text"
    
    #
    # main function to retrieve output
    #
    def getOutput(self):
        for s in range(1,self.nsteps+1):
            # i = row index
            i = s - 1
            
            # object = node or element
            obj_count = 1
            completed = 0
            filename = self.stepfile_template.format(s)
            with open(filename,'rb') as fObj:
                for line in fObj:
                    # find and set value
                    if "#" in line:
                        # comment line, skip to next line
                        continue
                    elif obj_count in self.obj_nums:
                        # this object was requested! add to array
                        # split string and convert to double
                        dummy = line.strip().split("  ")
                        value = numpy.float64(dummy[self.data_index])
                        # insert into array
                        objind = self.obj_nums.index(obj_count)
                        self.output[i,objind] = value
                        # iterate completed
                        completed += 1
                        # check if all tasks completed
                        if completed == self.nobjs:
                            break
                    # continue search
                    obj_count += 1
        return
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# stream file reader
#
class warpStreamOutput(warpFlatOutputHelpers):
    #
    # init
    #
    def __init__(self, output_dir, output_type, obj_nums, data_col, total_num_obj):
        # get templates, allocate numpy arrays, 
        
        self.output_dir  = output_dir
        self.output_type = output_type
        self.obj_nums    = obj_nums
        self.data_index  = data_col - 1
        
        # initialize
        self.nsteps = self._getNumSteps(self.output_dir)
        self.stepfile_template = self._outputFilenameTemplate()
        
        # must determine these for stream output
        self.total_num_obj  = total_num_obj # total number of nodes or elements (objects)
        self.total_num_cols = None # total number of data columns
        self.num_vals_per_step = self.total_num_obj * self.total_num_cols
        
        # preallocate
        self.output = numpy.zeros([self.nsteps,self.nobjs], dtype=numpy.float64)
        
        # execute
        self.getOutput()
        return

    #
    # props
    #
    @property
    def outputFormatType(self):
        """ define output format type """
        return "stream"
    
    #
    # main function to retrieve output
    #
    def getOutput(self):
        # some of this code is taken from the WARP3D manual
        for s in range(1,self.nsteps+1):
            i = s - 1 # output row index (step)
            filename = self.stepfile_template.format(s)
            with open(filename,'rb') as fObj:
                # rename some variables for convenience
                NVPS = self.num_vals_per_step
                DBL  = numpy.float64
                NNOD = self.total_num_obj
                NCOL = self.total_num_cols
                # read in and reshape data
                data = numpy.fromfile(file=fObj,count=NVPS,
                                        dtype=DBL).reshape(NNOD,NCOL)
                # insert desired values into array
                for j, objnum in enumerate(self.obj_nums):
                    objind = objnum - 1 
                    self.output[i,j] = data[objind,self.data_index]
        return