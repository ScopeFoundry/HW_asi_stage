from ScopeFoundry import HardwareComponent
from collections import OrderedDict

try:
    from .asi_xy_stage import ASIXYStage
except Exception as err:
    print("Cannot load required modules for ASI xy-stage:", err)

class ASIStage(HardwareComponent):
    
    name = 'asi_stage'
    
    filter_wheel_positions = OrderedDict(
        [('1_', 1),
        ('2_', 2),
        ('3_', 3),
        ('4_', 4),
        ('5_Closed', 5),
        ('6_', 6),
        ('7_', 7),])
    
    def setup(self):
    
        self.settings.New('x_position', 
                          initial = 0,
                          dtype=float, fmt='%10.1f', ro=False,
                          unit='um',
                          vmin=-1e10, vmax=1e10)
        
        self.settings.New('y_position',  dtype=float, unit='um', ro=False)
        self.settings.New('z_position',  dtype=float, unit='um', ro=False)        
        
        self.settings.New('filter_wheel', dtype=str, ro=False)
        
        self.settings.New('port', dtype=str, initial='COM4')
        
        
    def connect(self):
        S = self.settings
        
        # Open connection to hardware
        self.stage = ASIXYStage(port=S['port'], debug=S['debug_mode'])
                      
        # connect logged quantities
        
        S.x_position.connect_to_hardware(
            read_func = self.stage.getPosX,
            write_func =  self.stage.moveToX)
        S.y_position.connect_to_hardware(
            read_func = self.stage.getPosX,
            write_func =  self.stage.moveToX)
        S.z_position.connect_to_hardware(
            read_func = self.stage.getPosX,
            write_func =  self.stage.moveToX)
        
        S.filter_wheel.connect_to_hardware(
            write_func = self.write_fw_position
            )
        
        S['filter_wheel'] = '5_Closed'
        
        
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'stage'):
            self.stage.close()
            del self.stage
            
            
    def write_fw_position(self, pos_name):
        assert pos_name in self.filter_wheel_positions.keys()
        fw_number = self.filter_wheel_positions[pos_name]
        self.stage.moveFWto(fw_number)
        