from ScopeFoundry.scanning import BaseRaster2DSlowScan
import numpy as np
import time

class ASIStage2DScan(BaseRaster2DSlowScan):

    name = 'asi_stage_raster'
    
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(-15,15), v_limits=(-15,15),
                                      h_spinbox_step = 0.010, v_spinbox_step=0.010,
                                      h_unit="mm", v_unit="mm")

    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        self.stage = self.app.hardware['asi_stage']
        
    def move_position_h(self, h):
        S = self.stage.settings
        self.stage.other_observer = True
        try:
            S["x_target"] = h
            t0 = time.time()
            while True:
                if not self.stage.is_busy_xy():
                    break
                #print(time.time()-t0)
        finally:
            self.stage.other_observer = False
    
    def move_position(self, h,v):
        
        S = self.stage.settings
        self.stage.other_observer = True
        
        try:
            if not self.stage.settings['connected']:
                raise IOError("Not connected to ASI stage")
            
            #update target position
            S["x_target"] = h
            S["y_target"] = v

            # wait till arrived
            while True:
                time.sleep(0.025)
                if not self.stage.is_busy_xy():
                    break
        finally:
            self.stage.other_observer = False
            
    def move_position_start(self, h,v):
        self.move_position(h-0.02, v-0.02) # manual backlash correction
        self.move_position(h, v)
    def move_position_slow(self, h,v, dh,dv):
        self.move_position(h-0.02, v-0.02) # manual backlash correction
        self.move_position(h, v)

    def move_position_fast(self,  h,v, dh,dv):
        self.move_position_h(h)

class ASIStageDelay2DScan(ASIStage2DScan):

    name = 'asi_stage_delay_raster'
    
    def setup_figure(self):
        ASIStage2DScan.setup_figure(self)
        self.set_details_widget(
            widget=self.settings.New_UI(include=['pixel_time', 'frame_time']))
    
    def scan_specific_setup(self):
        self.settings.pixel_time.change_readonly(False)

    def collect_pixel(self, pixel_num, k, j, i):
        time.sleep(self.settings['pixel_time'])

    def update_display(self):
        pass    
        