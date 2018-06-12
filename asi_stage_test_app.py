from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure

class ASITestApp(BaseMicroscopeApp):
    
    name = 'asi_test_app'
    
    def setup(self):
        hw = self.add_hardware(ASIStageHW(self))
        hw.settings['port'] = 'COM5'
        
        self.add_measurement(ASIStageControlMeasure(self))
                
if __name__ == '__main__':
    import sys
    app = ASITestApp(sys.argv)
    app.exec_()