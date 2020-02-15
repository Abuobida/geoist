# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 09:18:25 2020

Funtion:
    
     3D grave&mag inversion using the space-domain approach with Bayes inference

Author:  Shi CHEN   @ IGP-CEA
         Bei ZHANGE @ IGP-CEA

####################################################
            MIT license
        Copyright @ GEOIST 2020 
         All right reserved 
####################################################

Module which contains the main classes of the pyBACGS
            
CLASS list:
    Model
    ModelBuilder
    ModelTs
    ModelTsCollection
    Source
    HexSource
    Field
    GravField
    MagField
    Mesh
    RegularMesh
    IrregulerMesh
    
    Using packages:
        ~geoist.inversion.abic.py
        ~geoist.inversion.walsh.py
        ~geoist.inversion.toeplitz.py
        
"""
import numpy as np
import json
from collections import namedtuple
from geoist.inversion import pfmodel_ts
from geoist.inversion import pfmodel
from geoist.inversion import walsh
from geoist.inversion import toeplitz as tptz
from geoist.others import utils


Dimension = namedtuple('Dimension', ['nx', 'ny', 'nz'])
Dimension2 = namedtuple('Dimension', ['nx', 'ny'])
Volume = namedtuple('Volume', ['xmin', 'xmax', 'ymin','ymax','zmin','zmax'])

Margin = namedtuple('Margin', ['left', 'right', 'down','up'])
Smooth = namedtuple('Smooth', ['dx','dy','dxy','dz','dt'])
Weight = namedtuple('Weight', ['dx','dy','dz','depth','obs','refer','bound'])

Celltype = ('tesseroid','prism')
Problem = ('3d','4d')
GravUnit = ('mgal','ugal')
MagUnit = ('nt','t')
LengthUnit = ('km','m','degree')


class Model(object):
    """the interface class for inversion with InvModel in pfmodel.py 
    """
    name = ''
    source = ''
    field = ''
    path = ''
    obs_stack = []
    ref_stack = []
    
    margin = None
    smooth = None
    weight  = None
    depth_constraint = None
    def __init__(self, ModelBuilder, name):
        self.source = ModelBuilder.bsource
        self.field = ModelBuilder.bfield
        self.cell = ModelBuilder.cell
        self.problem = ModelBuilder.problem
        self.name = name
        self.path = './data/gravity_inversion'
    def forward(self):
        self.model.forward()
    def inverse(self):
        pass
    def gen_kernel(self):
        self.model.gen_kernel()
    def set_datapath(self, data_path):
        self.path = data_path
    def set_refmod(self):
        pass
    def set_margin(self):
        pass
    def set_depth_constraint(self, kind = 1):
        if kind == 1:
            # depth constraint 第一类深度加权
            step = (self.source.vols[5] - self.source.vols[4])/self.source.dims[2]
            depths = np.linspace(self.source.vols[4]+step/2.,self.source.vols[5]-step/2.,self.source.dims[2])
            depth0 = 0
            alpha = 1
            self.depth_constraint = depths[0]**alpha/(depths+depth0)**alpha            
        else:
            print('kind 2 need to be coding...')
    def add_ref_stack(self, ref_model):
        self.ref_stack.append(ref_model)
        
    def set_smooth(self, smooth):
        self.smooth = smooth
    def set_weight(self, weight):
        self.weight = weight
    
    def run(self, mean = False):
        print('A instance of model with be generated!')
        if len(self.ref_stack) == 0:
            self.ref_stack.append(np.zeros([self.source.dims.nz, 
                                            self.source.dims.ny, 
                                            self.source.dims.nx]))
        
        self.model = pfmodel.InvModel(nzyx=[self.source.dims.nz,self.source.dims.ny,self.source.dims.nx],
                       source_volume=self.source.vols,
                       model_density=self.source.props,
                       refer_density=self.ref_stack[0],
                       depth_constraint=self.depth_constraint,
                       weights=self.weight,
                       smooth_on='m',
                       subtract_mean = mean,
                       data_dir=self.path)
        self.model.gen_mesh()
    
    def __str__(self):
        print('Source name = {}'.format(self.source.get_name()))
        print('Field name = {}'.format(self.field.get_name()))
        print('Model name = {}'.format(self.name))
        print('Problem type = {}'.format(self.problem))
        print('Cell type = {}'.format(self.cell))
        print('Working path = {}'.format(self.path))
        return "====Model Print by inv3d in geoist===="
        
    def save_to_json(self,filename):
        """Export instance of model class to JSON file
        """ 
        import pathlib
        from collections import Iterable
        def getdict(instance):
            if not isinstance(instance, pfmodel.InvModel):
                return getattr(instance, '__dict__', str(instance))
            else:
                dicttmp = instance.__dict__
                dicttmp['fname'] = 'obj'
                dicttmp['mesh'] = 'obj'
                dicttmp['smop'] = 'obj'
                dicttmp['kernel_op'] = 'obj'
                for key in dicttmp:
                    if isinstance(dicttmp[key], np.ndarray):
                        dicttmp[key] = dicttmp[key].tolist()
                    elif isinstance(dicttmp[key], set): 
                        dicttmp[key] = list(dicttmp[key])
                    if isinstance(dicttmp[key], dict):
                        for key1 in dicttmp[key]:
                            print(key1)
                            if isinstance(dicttmp[key][key1], np.ndarray):
                                dicttmp[key][key1] = dicttmp[key][key1].tolist()                       
                return(dicttmp)

        try:
            f = open(filename, mode = 'w')
            f.write(json.dumps(self, default = getdict))
            #f.write(json.dumps(self, default=lambda o: getattr(o, '__dict__', str(o))))
            f.close
        except IOError:
            print('No file : %s' %(filename))            
        except ValueError:
            print('check raw data file')
        except IndexError:
            print('check raw data file: possibly last line?')    
            
    def load_from_json(self, filename):
        """load model parameters and initialize it from JSON file
        TO_DO LIST 1:BEI
        """
        data_dict = {}
        try:
            f = open(filename, mode = 'r')
            data_dict = json.load(f)
            f.close
        except IOError:
            print('No file : %s' %(filename))            
        except ValueError:
            print('check raw data file')
        except IndexError:
            print('check raw data file: possibly last line?')           
        return data_dict
              
class ModelTs(Model):
        
    weights = {'obs':10,'dx':1,'dxy':1,'dt':200}       
    optimize_weights = ['obs','dx','dt']
    def __init__(self, ModelBuilder, name):
        super(ModelTs,self).__init__(ModelBuilder, name) 
        self.path = './data'
    def set_smooth(self, smooth_components):
        self.smooth = smooth_components
    def run(self):
        print('A instance of model with be generated!')
        self.model = pfmodel_ts.InvModelTS(nyx=[self.source.dims.ny,self.source.dims.nx],
                       source_volume=self.source.vols,
                       smooth_components=self.smooth,
                       weights=self.weights,
                       optimize_weights=self.weights.keys(),
                       data_dir=self.path)
        
        #self.model.gen_mesh()
    def save_to_json(self,filename):
        """Export instance of model class to JSON file
        """ 
        def getdict(instance):
            if not isinstance(instance, pfmodel_ts.InvModelTS):
                return getattr(instance, '__dict__', str(instance))

        try:
            f = open(filename, mode = 'w')
            f.write(json.dumps(self, default=getdict))
            #f.write(json.dumps(self, default=lambda o: getattr(o, '__dict__', str(o))))
            f.close
        except IOError:
            print('No file : %s' %(filename))            
        except ValueError:
            print('check raw data file')
        except IndexError:
            print('check raw data file: possibly last line?')         

class ModelsCollection(ModelTs):
    pass
            
        
class ModelBuilder(object):
    """
    """
    logging = []
    bsource = ''
    bfield = ''
    
    def __init__(self, use_gpu = 0):
        pfmodel.use_gpu = use_gpu 

    def set_source(self, source, dims, vols):
        self.bsource = source 
        self.bsource.dims = dims
        self.bsource.vols = vols
    def set_field(self, field):
        self.bfield = field

    def set_problem(self, cell = 'prism', problem = '3D'):
        if str.lower(cell) not in Celltype:
            raise ValueError('cell can be used tesseroid or prism!')
        else:
            self.cell = cell
        if str.lower(problem) not in Problem:
            raise ValueError('problem can be used 3D or 4D!')    
        else:
            self.problem = problem

    def add_obs(self, obs):
        pass
    def add_ref(self, ref):
        pass
    def builder(self, name = 'demo'):
        print('The {} problem model will be builded'.format(self.problem))
        if str.lower(self.problem) == Problem[0]:
            return Model(self, name)
        elif str.lower(self.problem) == Problem[1]: 
            return ModelTs(self, name)
        else:
            print('model builder error, please check the problem type!')
 

class Source(object):
    name = ''
    ftype = ''
    unit = ''
    def get_name(self):
        return self.name
    def get_unit(self):
        return self.unit
    def get_type(self):
        return self.ftype   

class HexSource(Source):
    dims = None
    vols = None
    props = None
    def __init__(self, name, unit = 'km'):
        self.ftype = 'hexahedron'
        self.name = name
    
        if str.lower(unit) not in LengthUnit:
            raise ValueError('unit can be used km or m or degrees!')
        else:
            self.unit = unit
            
    def show(self):
        print('source have {} and {}'.format(self.dims, self.vols))
    def gen_single_body(self, props = 1.0):
        self.props = np.zeros([self.dims.nz, self.dims.ny, self.dims.nx])
        
        self.props[round(self.dims.nz/2),round(self.dims.ny/2),round(self.dims.nx/2)] = props
        
    def load_from_txt(self):
        pass


class Field(object):
    unit = ''
    mesh = ''
    ftype =''
    name = ''
    def get_unit(self):
        return self.unit
    def get_mesh(self):
        return self.mesh.name
    def get_type(self):
        return self.ftype   
    def get_name(self):
        return self.name

class GravField(Field):
    
    def __init__(self, name, unit, mesh):
        self.name = name
        self.ftype = 'Gravity'
        if isinstance(mesh, Mesh):
            self.mesh = mesh
        else:
            raise ValueError('A instance of Mesh class must be used!')

        if str.lower(unit) not in GravUnit:
            raise ValueError('unit can be used mGal or uGal!')
        else:
            self.unit = unit
    def gen_data(self):
        pass

class MagField(Field):
    def __init__(self, name, unit, mesh):
        self.name = name
        self.ftype = 'Magnetism'
        self.mesh = mesh
        self.unit = unit
        
class Mesh(object):
    name = ''
    pass

class RegularMesh(Mesh):
    xset = [] #xmin, xmax, nx
    yset = [] #ymin, ymax, ny
    values = []
    def __init__(self, name, xset = [], yset = [], values = []):
        self.name = name
        self.xset = xset
        self.yset = yset
        self.values = values
    def show(self):
        print('the mesh length is {}'.format(len(self.values)))
    def load_mesh_from_grd(self):
        pass

class IrregulerMesh(Mesh): 
    x = []
    y = []
    values = []
    def __init__(self, name, x = [], y = [], values = []):
        self.name = name
        self.xset = x
        self.yset = y
        self.values = values
    def show(self):
        print('the mesh length is {}'.format(len(self.values)))
    def load_mesh_from_txt(self):
        pass

if __name__ == '__main__':
    mb = ModelBuilder()    
    t1mesh = RegularMesh('grid1')
    mb.set_field(GravField('test1.grav','mGal', t1mesh))
    
    dims = Dimension(2,4,8)
    vols = Volume(1,2,3,4,5,6)
    mb.set_source(HexSource('hex1.src','km'),dims, vols)    
        
    mb.set_problem('prism', '3D')
    
    m1 = mb.builder('model_test1')
    print(m1)
    weights = {'dx':23.54,'dy':860.,'dz':60.28,'depth':1.,'obs':1.69,'refer':0.67,'bound':1.0}
    m1.set_weight(weights)
    m1.source.gen_single_body(1.0)
    m1.set_depth_constraint()
    m1.run()     # generate model 
    
    m1.gen_kernel()
    m1.forward()
    
    m1.model.min_density = 0.
    m1.model.max_density = 1.
    orig_obs = m1.model.obs_data.copy()
    m1.model.walsh_transform()
    m1.model.abic_val
    list(m1.model._weights.keys())
    m1.model.do_linear_solve()
    m1.model.calc_abic()
    
    #export model information to JSON file
    m1.save_to_json('D://MyResearch//abic_inversion//notebook//m1json.txt')
    
    mb2 = ModelBuilder()
    mb2.set_field(GravField('test2.grav','mGal', RegularMesh('grid2')))
    smooth_components = ['dx','dy','dxy','dt']
    weights = {'obs':1,'dx':1,'dy':1,'dxy':1,'dt':1}

    dims = Dimension2(20,20)
    vols = Volume(-50000, 50000, -50000, 50000, 1000, 11000)
    mb2.set_source(HexSource('hex2.src','km'),dims, vols)    
        
    mb2.set_problem('Tesseroid', '4D')
    m2 = mb2.builder('model_test2')    
    print(m2)
    m2.set_weight(weights)
    m2.set_smooth(smooth_components)
    m2.run()
    m2.save_to_json('D://MyResearch//abic_inversion//notebook//m2json.txt')
    #m2 = mb.builder_ts()
    #m1.field.load_from_json()
