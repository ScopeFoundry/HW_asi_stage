from ScopeFoundry.scanning import BaseRaster2DSlowScan
import numpy as np
import time

class ASIStage2DScan(BaseRaster2DSlowScan):

    name = 'asi_stage_raster'
    
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(-15,15), v_limits=(-15,15),
                                      h_spinbox_step = 0.010, v_spinbox_step=0.010,
                                      h_unit="mm", v_unit="mm",circ_roi_size=0.002)

    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        self.stage = self.app.hardware['asi_stage']

    def new_pt_pos(self, x,y):
        # overwrite the function that lets you drag and drop the position
        # asi stage needs some time before
        S = self.stage.settings
        self.stage.other_observer = True
        try:
            if not self.stage.settings['connected']:
                raise IOError("Not connected to ASI stage")
            S["x_target"] = x
            S["y_target"] = y
            while self.stage.is_busy_xy():
                time.sleep(0.03)
            self.stage.correct_backlash(0.02)
        finally:
            self.stage.other_observer = False
            
    #def move_position(self, h,v):
    #    
    #    S = self.stage.settings
    #    self.stage.other_observer = True
    #    
    #    try:
    #        if not self.stage.settings['connected']:
    #            raise IOError("Not connected to ASI stage")
    #        
    #        #update target position
    #        #S["x_target"] = h
    #        #S["y_target"] = v
    #        self.stage.move_x(h)
    #        # wait till arrived
    #        while self.stage.is_busy_xy():
    #           time.sleep(0.03)
    #       self.stage.move_y(v)
    #       while self.stage.is_busy_xy():
    #           time.sleep(0.03)
    #   finally:
    #       self.stage.other_observer = False
            
    def move_position_start(self, h,v):
        print('start scan, moving to x={:.4f} , y={:.4f} '.format(h,v))
        self.stage.settings["x_target"] = h
        self.stage.settings["y_target"] = v
        #self.stage.move_x(h)
        #self.stage.move_y(v)
        while self.stage.is_busy_xy():
                time.sleep(0.03)
        self.stage.correct_backlash(0.02)
        
    def move_position_slow(self, h,v,dh,dv):   
        print('new line, moving to x={:.4f} , y={:.4f} '.format(h,v))
        self.stage.settings["x_target"] = h-0.02
        self.stage.settings["y_target"] = v
        #self.stage.move_y(v)
        #self.stage.move_x(h-0.02)
        while self.stage.is_busy_xy():
                time.sleep(0.03)
        #self.stage.move_x(h)
        self.stage.settings["x_target"] = h
        while self.stage.is_busy_xy():
                time.sleep(0.03)

    def move_position_fast(self, h,v,dh,dv):
        # move without explicitely waiting for stage to finish
        # otherwise the internal PID settings of the stage limits the pixel speed 
        self.stage.settings["x_target"] = h
        time.sleep(1.2*dh / self.stage.settings['xy_speed'])
        
                
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
        