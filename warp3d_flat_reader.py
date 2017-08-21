"""
Vincente Pericoli
UC Davis

reader to get output from warp3d flat files.    
quick and dirty
"""


#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# imports
#
import os, fnmatch, numpy

#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# helper routines
#
def composeWriteString(iterable_of_strings):
    """ iterable of strings converted to CSV write string """
    write_string = ""
    for s in iterable_of_strings:
        write_string += s
        write_string += ", "
    write_string += "\n"
    return write_string

def writeCSVOutput(filename, header, array):
    # need headers, iterable of arrays, step numbers
    # arrays are populated. write to CSV
    nsteps = array.shape[0]
    ncols  = array.shape[1]
    write_num_template = "{:>13.6e}"
    
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
# main function
#
class warpFlatOutput(object):
    #
    # init
    #
    def __init__(self, output_dir, output_type, obj_nums, data_col):
        # get templates, allocate numpy arrays, 
        
        self.output_dir  = output_dir
        self.output_type = output_type
        self.obj_nums    = obj_nums
        self.data_index  = data_col - 1
        
        # initialize
        self.nsteps = self._getNumSteps(self.output_dir)
        self.flat_template = self._flatFileTemplate()
        
        # preallocate
        self.output = numpy.zeros([self.nsteps,self.nobjs], dtype=numpy.float64)
        
        # execute
        self.getOutput()

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
        wnd = len(fnmatch.filter(os.listdir(dirpath), 'wnd*_text'))
        wnr = len(fnmatch.filter(os.listdir(dirpath), 'wnr*_text'))
        num_steps = max((wnd,wnr))
        if (0 in (wnd,wnr)):
            if ((wnd==0) and (wnr==0)):
                raise RuntimeError("no output found")
        elif (wnd != wnr):
            raise RuntimeError("wnd wnr step number mismatch")
        return num_steps
    
    def _composeCSVString(self, iterable_of_strings):
        """ iterable of strings converted to CSV write string """
        write_string = ""
        for s in iterable_of_strings:
            write_string += s
            write_string += ", "
        write_string += "\n"
        return write_string
    
    def _flatFileTemplate(self):
        """ template flat file name format """
        template_dict = {"reaction"       : "wnr{:05d}_text",
                         "displacement"   : "wnd{:05d}_text",
                         "cohesive_state" : "wem{:05d}_text_cohesive"}
        if not (self.output_type in template_dict.keys()):
            raise RuntimeError("Invalid output_type")
        return template_dict[self.output_type]

    def sumOutput(self):
        """ implicitly assumed that we want to sum objects accross step """
        self.output = self.output.sum(axis=1,keepdims=True)
        return
    
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
            filename = self.flat_template.format(s)
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
                        objind = self._obj_nums.index(obj_count)
                        self.output[i,objind] = value
                        # iterate completed
                        completed += 1
                        # check if all tasks completed
                        if completed == self.nobjs:
                            break
                    # continue search
                    obj_count += 1
        return