from ScopeFoundry import HardwareComponent
from collections import OrderedDict
import threading
import time
import numpy as np

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
    
    def __init__(self, app, debug=False, name=None, enable_xy=True, enable_z=True, enable_fw=False, swap_xy=False, invert_x=False,invert_y=False):
        self.enable_xy = enable_xy
        self.enable_z = enable_z
        self.swap_xy = swap_xy
        self.invert_x = invert_x
        self.invert_y = invert_y
        
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
        xy_kwargs = dict(initial = 0.00000,
                          dtype=float,
                          unit='mm',
                          spinbox_decimals = 5,
                          spinbox_step=0.10000)
        x_pos = self.settings.New('x_position', ro=True, **xy_kwargs)        
        y_pos = self.settings.New('y_position', ro=True, **xy_kwargs)
        
        x_target = self.settings.New('x_target', ro=False, **xy_kwargs)        
        y_target = self.settings.New('y_target', ro=False, **xy_kwargs)
        
        self.settings.New("speed_xy", ro=False, initial=3.00, unit='mm/s', spinbox_decimals=3, spinbox_step=0.10, vmin=0.00, vmax=5.00)
        self.settings.New("acc_xy", ro=False, initial=10, unit='ms', spinbox_decimals=1)
        self.settings.New("backlash_xy", ro=False, initial=0.00, unit='mm', spinbox_decimals=3)
        
        self.settings.New("speed_x",  ro=False, initial=3.00, unit='mm/s', spinbox_decimals=3, spinbox_step=0.10, vmin=0.00, vmax=5.00)
        self.settings.New("speed_y",  ro=False, initial=3.00, unit='mm/s', spinbox_decimals=3, spinbox_step=0.10, vmin=0.00, vmax=5.00)
        
        if self.enable_z:
            z_pos = self.settings.New('z_position', ro=True, **xy_kwargs)
            z_target = self.settings.New('z_target', ro=False, **xy_kwargs)  
            backlash_z = self.settings.New('backlash_z', ro=False, initial=0.00, unit='mm', spinbox_decimals=3)
            speed_z = self.settings.New("speed_z", ro=False, initial=1.20000, unit='mm/s', spinbox_decimals=5, spinbox_step=0.10000, vmin=0.00000, vmax=3.00000)
            
        
        self.settings.New('port', dtype=str, initial='COM4')
        
        self.add_operation("Halt XY", self.halt_xy)
        if self.enable_z: self.add_operation("Halt Z", self.halt_z)
        self.add_operation("Home XY", self.home_xy)
        if self.enable_z: self.add_operation("Home Z", self.home_z)
        
        # TODO Filter wheel is not configured
        
        
    def connect(self):
        S = self.settings
        
        # Open connection to hardware
        self.stage = ASIXYStage(port=S['port'], debug=S['debug_mode'])
                      
        # connect logged quantities
        S.x_position.connect_to_hardware(
            read_func = self.read_pos_x)
        S.y_position.connect_to_hardware(
            read_func = self.read_pos_y)
        
        def set_debug_mode(val):
            self.stage.debug = val
        S.debug_mode.connect_to_hardware(
            write_func = set_debug_mode)
            
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
        S.backlash_xy.connect_to_hardware(
            write_func = self.stage.set_backlash_xy
            )
        S.backlash_xy.write_to_hardware()
        S.speed_xy.connect_to_hardware(
            write_func = self.set_speed_xy
            )
        S.speed_xy.write_to_hardware()
        
        S.speed_x.connect_to_hardware(
            read_func = self.stage.get_speed_x,
            write_func = self.set_speed_x
        )
        S.speed_x.write_to_hardware()

        S.speed_y.connect_to_hardware(
            read_func = self.stage.get_speed_y,
            write_func = self.set_speed_y
        )
        S.speed_y.write_to_hardware()
                    
        '''# xbox controller speed writing
        xbS = self.app.measurements['xbcontrol_mc'].settings
        xbS.speed_x.connect_to_hardware(
            write_func = self.set_speed_x
            )
        xbS.speed_x.write_to_hardware()'''
        
        
        S.acc_xy.connect_to_hardware(
            write_func = self.set_acc_xy
            )
        S.acc_xy.write_to_hardware()

        
        if self.enable_z:
            S.z_position.connect_to_hardware(
                read_func = self.stage.read_pos_z)
            S.z_position.read_from_hardware()
            S['z_target'] = S['z_position']
            S.z_target.connect_to_hardware(
                write_func = self.stage.move_z
                )
            S.backlash_z.connect_to_hardware(
                write_func = self.stage.set_backlash_z
                )
            S.backlash_z.write_to_hardware()
            
            S.speed_z.connect_to_hardware(
                write_func = self.set_speed_z
                )
            S.speed_z.write_to_hardware()
        
        S.x_position.read_from_hardware()
        S.y_position.read_from_hardware()
        
        
        
        # if other observer is actively reading position,
        # don't update as frequently in update_thread
        self.other_observer = False
        
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        self.update_thread.start()
        
        self.is_connected = True
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread

        
        if hasattr(self, 'stage'):
            self.stage.close()
            del self.stage
            
        self.is_connected = False
            
    def write_fw_position(self, pos_name):
        assert pos_name in self.filter_wheel_positions.keys()
        fw_number = self.filter_wheel_positions[pos_name]
        self.stage.moveFWto(fw_number)
        
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            self.settings.y_position.read_from_hardware()
            self.settings.x_position.read_from_hardware()
            if self.enable_z:
                    #print("reading z pos")
                    self.settings.z_position.read_from_hardware()
            if self.other_observer:
                # it's better not to query the asi stage while it's being observed by e.g the scanning app
                time.sleep(1)
            else:
                time.sleep(0.2)

    def halt_xy(self):
        self.stage.halt_xy()
    def halt_z(self):
        self.stage.halt_z()
    def home_xy(self):
        self.stage.home_and_center_xy()
    def home_z(self):
        self.stage.home_and_wait_z()
        time.sleep(0.25)
        self.stage.set_here_z(25)
    
    def set_speed_xy(self, speed_x, speed_y = None):
        if speed_y == None:
            self.stage.set_speed_xy(speed_x, speed_x)
        else:
            self.stage.set_speed_xy(speed_x,speed_y)
        self.settings.speed_x.read_from_hardware()
        self.settings.speed_y.read_from_hardware()
    
    def set_speed_x(self, speed_x):
        self.stage.set_speed_x(speed_x)
    
    def set_speed_y(self, speed_y):
        self.stage.set_speed_y(speed_y)
    
    def set_speed_z(self, speed_z):
        self.stage.set_speed_z(speed_z)
        
    def set_acc_xy(self, acc):
        self.stage.set_acc_xy(acc,acc)
        
    def read_pos_x(self):
        if not self.swap_xy and not self.invert_x:
            return self.attempt_10_times(self.stage.read_pos_x)
        elif not self.swap_xy:
            return -self.attempt_10_times(self.stage.read_pos_x)
        elif not self.invert_x:
            return self.attempt_10_times(self.stage.read_pos_y)
        else:
            return -self.attempt_10_times(self.stage.read_pos_y)

    def read_pos_y(self):
        if not self.swap_xy and not self.invert_y:
            return self.attempt_10_times(self.stage.read_pos_y)
        elif not self.swap_xy:
            return -self.attempt_10_times(self.stage.read_pos_y)
        elif not self.invert_y:
            return self.attempt_10_times(self.stage.read_pos_x)
        else:
            return -self.attempt_10_times(self.stage.read_pos_x)

    def move_x(self, x):
        if not self.swap_xy and not self.invert_x:
            return self.attempt_10_times(self.stage.move_x, x)
        elif not self.swap_xy:
            return self.attempt_10_times(self.stage.move_x,-x)
        elif not self.invert_x:
            return self.attempt_10_times(self.stage.move_y, x)
        else:
            return self.attempt_10_times(self.stage.move_y, -x)
        
    def move_x_rel(self, x):
        if not self.swap_xy and not self.invert_x:
            return self.attempt_10_times(self.stage.move_x_rel, x)
        elif not self.swap_xy:
            return self.attempt_10_times(self.stage.move_x_rel, -x)
        elif not self.invert_x:
            return self.attempt_10_times(self.stage.move_y_rel, -x)
        else:
            return self.attempt_10_times(self.stage.move_y_rel, x)
    
    def move_y(self, x):
        if not self.swap_xy and not self.invert_y:
            return self.attempt_10_times(self.stage.move_y, x)
        elif not self.swap_xy:
            return self.attempt_10_times(self.stage.move_y, -x)
        elif not self.invert_y:
            return self.attempt_10_times(self.stage.move_x, x)
        else:
            return self.attempt_10_times(self.stage.move_x, -x)
        
    def move_y_rel(self, x):
        if not self.swap_xy and not self.invert_y:
            return self.attempt_10_times(self.stage.move_y_rel, x)
        elif not self.swap_xy:
            return self.attempt_10_times(self.stage.move_y_rel, -x)
        elif not self.invert_y:
            return self.attempt_10_times(self.stage.move_x_rel, -x)
        else: 
            return self.attempt_10_times(self.stage.move_x_rel, x)
    
    def move_z(self, z):
        return self.attempt_10_times(self.stage.move_z, z)
    
    def move_z_rel(self, x):
        return self.attempt_10_times(self.stage.move_z_rel, x)
    
    def is_busy_xy(self):
        return self.attempt_10_times(self.stage.is_busy_xy)
    
    def is_busy_z(self):
        return self.attempt_10_times(self.stage.is_busy_z)
    
    def correct_backlash(self,backlash):
        self.move_x_rel(-backlash)
        self.move_y_rel(-backlash)
        while self.stage.is_busy_xy():
            time.sleep(0.03)
        self.move_x_rel(backlash)
        self.move_y_rel(backlash)    
        while self.stage.is_busy_xy():
            time.sleep(0.03)
    
        
    def attempt_10_times(self, func, *args,**kwargs):
        attempts = 0
        while attempts < 10:
            try:
                retval = func(*args,**kwargs)
                return retval
            except:
                attempts +=1
    
    
    def linear_move_abs(self, x, y, z=None, speed=None):
        
        if speed is None:
            speed = self.settings['speed_xy']
        
        # store original speed
        sx0 = self.settings['speed_x']
        sy0 = self.settings['speed_y']
        sz0 = self.settings['speed_z']
        # original position
        x0 = self.settings['x_position']
        y0 = self.settings['y_position']
        z0 = self.settings['z_position']

        # compute velocity vector and set speeds
        dx = abs(x - x0)
        dy = abs(y - y0)
        if z is None:
            dz = 0
        else:
            dz = abs(z - z0)
        dL = np.sqrt(dx**2 + dy**2+dz**2)
        dt = dL/speed
        
        print("dt ", dt)
        print("dL", dL, dx, dy, dz)
        if dx/dt > 1e-4:
            self.settings['speed_x'] = dx/dt
        if dy/dt > 1e-4:
            self.settings['speed_y'] = dy/dt
        if dz/dt > 1e-4:
            self.settings['speed_z'] = dz/dt
        print("speed", dx/dt, dy/dt, dz/dt)
            
        # initiate move
        self.settings['x_target'] = x
        self.settings['y_target'] = y
        if z is not None:
            self.settings['z_target'] = z
            
        # wait?
        
        # # restore original speeds
        # self.settings['speed_x'] = sx0
        # self.settings['speed_y'] = sy0
        # self.settings['speed_z'] = sz0
        