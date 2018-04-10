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
class warpReadersBase(object):
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
    def int_types(self):
        return (int, numpy.int32, numpy.int64)
    
    @property
    def output(self):
        """ the output data """
        return self._output
        
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
    def obj_nums(self, o_nums):
        iterable = hasattr(o_nums,'__iter__') 
        if( type(o_nums) is str ):
            self._obj_nums = o_nums
        elif( not iterable ):
            self._obj_nums = (o_nums,)
        elif( iterable ):
            self._obj_nums = o_nums
        else:
            raise TypeError("illegal type obj_nums")
        return
        
    @property
    def data_cols(self):
        return self._data_cols
    @data_cols.setter
    def data_cols(self, d_cols):
        # set data indices
        if( type(d_cols) in self.int_types ):
            self._data_cols = numpy.asarray( (d_cols,) )
        elif( hasattr(d_cols,'__iter__') ):
            self._data_cols = numpy.asarray(d_cols)
        else:
            raise TypeError("unknown dtype data_cols")
        return
        
    @property
    def data_inds(self):
        return self.data_cols - 1
        
    @property
    def writeNumTemplate(self):
        return "{:>13.6e}"
    
    #
    # helper functions
    #
    def _getFileList(self, dirpath):
        """ obtain the list of output files """
        template = self._outputFilenameTemplate()
        file_list = sorted( fnmatch.filter(os.listdir(dirpath), template) )
        if( len(file_list) == 0 ):
            raise RuntimeError("no output found")
        return tuple(file_list)
    
    def _nodalOutputFilenameTemplate(self):
        """ filename format template """
        fmt = self.outputFormatType
        template_dict = {"stress"         : "wns*_" + fmt,
                         "reaction"       : "wnr*_" + fmt,
                         "displacement"   : "wnd*_" + fmt}
        if not (self.output_type in template_dict.keys()):
            raise RuntimeError("Invalid output_type")
        return template_dict[self.output_type]
        
    def _elemOutputFilenameTemplate(self):
        """ filename format template """
        fmt = self.outputFormatType
        template_dict = {"stress"         : "wes*_" + fmt,
                         "cohesive_state" : "wem*_" + fmt + "_cohesive",
                         "bilinear_state" : "wem*_" + fmt + "_bilinear"}
        if not (self.output_type in template_dict.keys()):
            raise RuntimeError("Invalid output_type")
        return template_dict[self.output_type]
        
    def _outputFilenameTemplate(self):
        """ filename format template """
        if( "nod" in self.obj_type ):
            return self._nodalOutputFilenameTemplate()
        elif( "ele" in self.obj_type ):
            return self._elemOutputFilenameTemplate()
        raise RuntimeError("Invalid object type: " + self.obj_type)
        return
        
    def _composeCSVString(self, iterable_of_strings):
        """ iterable of strings converted to CSV write string """
        write_string = ""
        for s in iterable_of_strings:
            write_string += s
            write_string += ", "
        write_string += "\n"
        return write_string
        
    def sumOutput(self):
        """ implicitly assumed that we want to sum objects across step """
        self._output = self._output.sum(axis=1,keepdims=True)
        return
        
    def writeCSVOutput(self, filename, header, array):
        # need headers, iterable of arrays, step numbers
        # arrays are populated. write to CSV
        
        array = numpy.squeeze(array)
        nsteps,ncols = array.shape
        
        write_num_template = self.writeNumTemplate
        
        header = header.rstrip() + "\n"
        
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
                write_string = self._composeCSVString(strlist)
                
                # write
                fObj.write(write_string)
        return

# for backwards compatibility:        
warpFlatOutputHelpers = warpReadersBase
    
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# flat file reader
#
class warpTextOutput(warpReadersBase):
    #
    # init
    #
    def __init__(self, output_dir, output_type, obj_type, obj_nums, data_cols):
        # get templates, allocate numpy arrays, 
        
        self.output_dir   = output_dir
        self.output_type  = output_type
        self.obj_nums     = obj_nums
        self.obj_type     = obj_type
        self.data_cols    = data_cols # data_inds automatically set
        
        # define object counts and indices
        if( obj_nums == 'all' ):
            raise NotImplementedError("'all' undefined for text output.")
        else:
            self.nobjs    = len(self.obj_nums)
            self.obj_inds = numpy.asarray(self.obj_nums) - 1
        
        # obtain list of output files
        self.__file_list = self._getFileList( self.output_dir )
        
        # initialize
        self.ndata  = len(self.data_inds)
        self.nsteps = len(self.__file_list)
        
        # preallocate
        self._output = numpy.zeros( [self.nsteps,self.nobjs,self.ndata], 
                                    dtype=numpy.float64 )
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
        # loop thru output files
        for i,fn in enumerate(self.__file_list):
        
            # object = node or element
            obj_count = 1
            completed = 0
            
            with open(fn,'rb') as fObj:
                for line in fObj:
                    # find and set value
                    if( "#" in line ):
                        # comment line, skip to next line
                        continue
                    elif( obj_count in self.obj_nums ):
                        # this object was requested! add to array
                        # split string and convert to double
                        dummy  = line.strip().split()
                        values = numpy.float64(dummy)[self.data_inds]
                        # insert into array
                        objind = self.obj_nums.index(obj_count)
                        self._output[i,objind,:] = values
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
class warpStreamOutput(warpReadersBase):
    #
    # init
    #
    def __init__(self, output_dir, output_type, obj_type, obj_nums, data_cols, total_num_obj, total_num_cols=None):
        """ 
        Inputs:
             output_dir : string of output directory
            output_type : string of output type (e.g. 'stress')
               obj_type : string, "nodes" or "elements"
               obj_nums : list of objects (i.e. node/element numbers) to save; or "all"
              data_cols : list of data column indices you wish to save (column 1 is index 1)
          total_num_obj : the total number of objects (i.e. nodes/elements) in the output
         total_num_cols : the total number of columns in the output
        """     
        
        self.output_dir  = output_dir
        self.output_type = output_type
        self.obj_nums    = obj_nums
        self.obj_type    = obj_type
        self.data_cols   = data_cols # data_inds automatically set
        
        # define object counts and indices
        if( obj_nums == 'all' ):
            self.nobjs    = total_num_obj
            self.obj_inds = None
        else:
            self.nobjs    = len(self.obj_nums)
            self.obj_inds = numpy.asarray(self.obj_nums) - 1
        
        # total number of nodes or elements (objects)
        self.total_num_obj  = total_num_obj
        
        # total number of data columns in stream output
        if( total_num_cols is None):
            self.total_num_cols = self.getNumCols()
        else:
            self.total_num_cols = int( total_num_cols )
        
        # obtain list of output files
        self.__file_list = self._getFileList( self.output_dir )
        
        # initialize
        self.ndata  = len(self.data_inds)
        self.nsteps = len(self.__file_list)
        self.num_vals_per_step = self.total_num_obj * self.total_num_cols
        
        # preallocate
        self._output = numpy.zeros([self.nsteps,self.nobjs,self.ndata], dtype=numpy.float64)
        
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
    # helper funs
    #
    def getNumCols(self):
        """ total number of data columns """
        if( self.output_type == "stress" ):
            return 26
        elif( self.output_type == "reaction" ):
            return 3
        elif( self.output_type == "displacement" ):
            return 3
        else:
            raise NotImplementedError("Unknown Output Type. Please provide total_num_cols in input.")
        return None
    
    #
    # main function to retrieve output
    #
    def getOutput(self):
        # some of this code is taken from the WARP3D manual
        
        # rename some variables for convenience
        NVPS = self.num_vals_per_step
        DBL  = numpy.float64
        NOBJ = self.total_num_obj
        NCOL = self.total_num_cols
        
        # do we just save everything?
        save_all_objs = (self.obj_nums == 'all')
        
        # loop thru output files
        for i, fn in enumerate(self.__file_list):
            with open(fn,'rb') as fObj:
                # read in and reshape data
                data = numpy.fromfile(file=fObj,count=-1,dtype=DBL)
                # try-except on reshape as a sanity check.
                # if this fails, user has incorrect info about data file.
                try:
                    data = data.reshape(NOBJ,NCOL)
                except ValueError:
                    err_msg = ( "The data file contains " + str(len(data)) + " items, "
                              + "but you have declared " + str(NVPS) + " items. "
                              + "Either total_num_obj or total_num_cols is incorrect." )
                    raise ValueError(err_msg)
                # insert desired values into array
                if( save_all_objs ):
                    self._output[i,:,:] = data[:,self.data_inds]
                else:
                    # this is required because numpy is fucking insane
                    try:
                        self._output[i,:,:] = data[self.obj_inds, self.data_inds]
                    except ValueError:
                        assert(self._output.shape[1] == len(self.obj_inds))
                        assert(self._output.shape[2] == len(self.data_inds))
                        self._output[i,:,:] = numpy.reshape(
                                                data[self.obj_inds, self.data_inds], 
                                                (len(self.obj_inds),len(self.data_inds)) )
        return