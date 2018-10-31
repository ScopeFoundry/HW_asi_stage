from ScopeFoundry import HardwareComponent
from collections import OrderedDict
import threading
import time

try:
    from .asi_stage_dev import ASIXYStage
except Exception as err:
    print("Cannot load required modules for ASI xy-stage:", err)

class ASIStageHW(HardwareComponent):
    
    name = 'asi_stage'
    
    filter_wheel_positions = OrderedDict(
        [('1_', 1),
        ('2_', 2),
        ('3_', 3),
        ('4_', 4),
        ('5_Closed', 5),
        ('6_', 6),
        ('7_', 7),])
    
    def __init__(self, app, debug=False, name=None, enable_xy=True, enable_z=True, enable_fw=True):
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
    
    
        xy_kwargs = dict(initial = 0,
                          dtype=float,
                          unit='mm',
                          spinbox_decimals = 4,
                          spinbox_step=0.1)
        x_pos = self.settings.New('x_position', ro=True, **xy_kwargs)        
        y_pos = self.settings.New('y_position', ro=True, **xy_kwargs)
        
        x_target = self.settings.New('x_target', ro=False, **xy_kwargs)        
        y_target = self.settings.New('y_target', ro=False, **xy_kwargs)
        
        
        
        #self.settings.New('z_position',  dtype=float, unit='um', ro=False, reread_from_hardware_after_write=True)        
        
        #self.settings.New('filter_wheel', dtype=str, ro=False)
        
        self.settings.New('port', dtype=str, initial='COM4')
        
        self.add_operation("Halt XY", self.halt_xy)
        
    def connect(self):
        S = self.settings
        
        # Open connection to hardware
        self.stage = ASIXYStage(port=S['port'], debug=S['debug_mode'])
                      
        # connect logged quantities
        
        S.x_position.connect_to_hardware(
            read_func = self.read_pos_x)
        S.y_position.connect_to_hardware(
            read_func = self.read_pos_y)
        
        try:
            S.x_position.read_from_hardware()
            S.y_position.read_from_hardware()
        except Exception as err:
            print('cannot read xy position')
            
        S['x_target'] = S['x_position']
        S['y_target'] = S['y_position']

        S.x_target.connect_to_hardware(
            write_func = self.move_x
            )
        S.y_target.connect_to_hardware(
            write_func = self.move_y
            )

        
#         S.z_position.connect_to_hardware(
#             read_func = self.stage.getPosZ,
#             write_func =  self.stage.moveToZ)
        
#         S.filter_wheel.connect_to_hardware(
#             write_func = self.write_fw_position
#             )
#         
#         S['filter_wheel'] = '5_Closed'
        
        S.x_position.read_from_hardware()
        S.y_position.read_from_hardware()
        
        # set reasonable values for moving the stage
        self.stage.set_speed(0.1, 0.1) # in mm, standard 7mm/s, this is more reasonable
        self.stage.set_backlash_xy(0.0, 0.0) # disable backlash correction
        self.stage.set_acc(10,10) #in ms
        # if other observer is actively reading position,
        # don't update as frequently in update_thread
        self.other_observer = False
        
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        self.update_thread.start()

        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread

        
        if hasattr(self, 'stage'):
            self.stage.close()
            del self.stage
            
            
    def write_fw_position(self, pos_name):
        assert pos_name in self.filter_wheel_positions.keys()
        fw_number = self.filter_wheel_positions[pos_name]
        self.stage.moveFWto(fw_number)
        
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            self.settings.x_position.read_from_hardware()
            self.settings.y_position.read_from_hardware()
            if self.other_observer:
                time.sleep(1.0)
            else:
                time.sleep(0.050)

    def halt_xy(self):
        self.stage.halt_xy()
        
    def read_pos_x(self):        
        return self.attempt_10_times(self.stage.read_pos_x)

    def read_pos_y(self):
        return self.attempt_10_times(self.stage.read_pos_y)

    def move_x(self, x):
        return self.attempt_10_times(self.stage.move_x, x)

    def move_y(self, y):
        return self.attempt_10_times(self.stage.move_y, y)
    
    def is_busy_xy(self):
        return self.attempt_10_times(self.stage.is_busy_xy)
    
    
    def attempt_10_times(self, func, *args,**kwargs):
        attempts = 0
        while attempts < 10:
            try:
                retval = func(*args,**kwargs)
                if attempts != 0:
                    print('ASI stage needed attempts:'+str(attempts))
                return retval
            except:
                attempts +=1
    
        