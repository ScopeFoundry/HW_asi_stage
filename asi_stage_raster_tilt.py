from ScopeFoundry.scanning import BaseRaster2DSlowScan
import time
import numpy as np

class ASIStage2DScanTilt(BaseRaster2DSlowScan):

    name = 'asi_stage_raster'
    
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, 
                                      h_limits=(-37,37), v_limits=(-23,37),
                                      #h_limits=(-15,15), v_limits=(-15,15),
                                      h_spinbox_step = 0.010, v_spinbox_step=0.010,
                                      h_unit="mm", v_unit="mm",circ_roi_size=0.002)

    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        self.stage = self.app.hardware['asi_stage']

        self.settings.New('tilt_correction', dtype=bool)
        self.settings.New('tilt_point1', dtype=float, array=True, initial=[0,0,0])
        self.settings.New('tilt_point2', dtype=float, array=True, initial=[0,0,0])
        self.settings.New('tilt_point3', dtype=float, array=True, initial=[0,0,0])
        
        self.add_operation('Mark Focus 1', self.mark_tilt_point1)
        self.add_operation('Mark Focus 2', self.mark_tilt_point2)
        self.add_operation('Mark Focus 3', self.mark_tilt_point3)
        
        self.add_operation('fix focus', self.move_z_tilt)



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
            if self.settings['tilt_correction']:
                self.stage.settings['speed_z'] = 1.0
                self.move_z_tilt()
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
        if self.settings['tilt_correction']:
            self.stage.settings['speed_z'] = 1.0
            self.move_z_tilt()
            time.sleep(0.3)        
        
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
        if self.settings['tilt_correction']:
            self.stage.settings['speed_z'] = 1.0
            self.move_z_tilt()
            time.sleep(0.3)
            
    def move_position_fast(self, h,v,dh,dv):
        # move without explicitely waiting for stage to finish
        # otherwise the internal PID settings of the stage limits the pixel speed 
        if self.settings['tilt_correction']:
            self.move_z_tilt()
            time.sleep(0.01)
        self.stage.settings["x_target"] = h
        time.sleep(1.2*abs(dh) / self.stage.settings['speed_xy'])

    def get_stage_pos_xyz(self):
        x = self.stage.settings['x_position']
        y = self.stage.settings['y_position']
        z = self.stage.settings['z_position']
        return (x,y,z)

    def compute_tilt_plane(self):
        p1 = self.settings['tilt_point1']
        p2 = self.settings['tilt_point2']
        p3 = self.settings['tilt_point3']
        tilt_coords = np.array([p1,p2,p3])
        flat_coords = tilt_coords.copy()
        flat_coords[:,2] = 0 # set z=0 for flat plane coords
        
        import skimage.transform
        tf = skimage.transform.estimate_transform(
            'similarity', flat_coords, tilt_coords)
        self.tilt_transform = tf

    def mark_tilt_point1(self):
        self.settings['tilt_point1'] = self.get_stage_pos_xyz()
        print(self.get_stage_pos_xyz())
        self.compute_tilt_plane()

    def mark_tilt_point2(self):
        self.settings['tilt_point2'] = self.get_stage_pos_xyz()
        self.compute_tilt_plane()

    def mark_tilt_point3(self):
        self.settings['tilt_point3'] = self.get_stage_pos_xyz()
        self.compute_tilt_plane()
        
    def move_z_tilt(self):
        print("move_z_tilt")
        tf = self.tilt_transform
        x,y,z = self.get_stage_pos_xyz()
        
        x1,y1,z1,_ = tf.params @ [x,y,0,1]
        print("move_z_tilt", x,y,z, "-->", x1,y1,z1)
        
        print(f"{z=} {z1=}")
        if abs(z1-z) < 2:
            self.stage.settings['z_target'] = z1
        else:
            raise ValueError(f"move_z_tilt moved too far. current {z=} mm; computed {z1=} mm; delta {z1-z} mm")
            
    def compute_z_tilt(self, x,y):
        tf = self.tilt_transform        
        x1,y1,z1,_ = tf.params @ [x,y,0,1]
        return z1
    
class ASIStageDelay2DScanTilt(ASIStage2DScanTilt):

    name = 'asi_stage_delay_raster_tilt'
    
    def setup_figure(self):
        ASIStage2DScanTilt.setup_figure(self)
        self.set_details_widget(
            widget=self.settings.New_UI(include=['pixel_time', 'frame_time']))
    
    def scan_specific_setup(self):
        self.settings.pixel_time.change_readonly(False)

    def collect_pixel(self, pixel_num, k, j, i):
        time.sleep(self.settings['pixel_time'])

    def update_display(self):
        pass
     