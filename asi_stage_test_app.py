from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStageDelay2DScan

class ASITestApp(BaseMicroscopeApp):
    
    name = 'asi_test_app'
    
    def setup(self):
        hw = self.add_hardware(ASIStageHW(self))
        hw.settings['port'] = 'COM5'
        
        self.add_measurement(ASIStageControlMeasure(self))
        
        self.add_measurement(ASIStageDelay2DScan(self))
                
if __name__ == '__main__':
    import sys
    app = ASITestApp(sys.argv)
    app.exec_()