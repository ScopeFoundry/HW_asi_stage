from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path


class ASIStageControlMeasure(Measurement):
    
    name = 'ASI_Stage_Control'
    
    def __init__(self, app, name=None, hw_name='asi_stage'):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)

    
    def setup(self):
        
        self.settings.New('jog_step_xy',
                          dtype=float, unit='mm', 
                          initial=0.1, spinbox_decimals=4)

        self.settings.New('jog_step_z',
                          dtype=float, unit='mm', 
                          initial=0.1, spinbox_decimals=4)


        self.stage = self.app.hardware[self.hw_name]

        
    def setup_figure(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, 'asi_stage_control.ui'))
        
        self.stage.settings.connected.connect_to_widget(
            self.ui.asi_stage_connect_checkBox)
        
        self.stage.settings.x_position.connect_to_widget(
            self.ui.x_pos_doubleSpinBox)
        self.stage.settings.y_position.connect_to_widget(
            self.ui.y_pos_doubleSpinBox)

        self.stage.settings.z_position.connect_to_widget(
            self.ui.z_pos_doubleSpinBox)

        
        self.settings.jog_step_xy.connect_to_widget(
            self.ui.xy_step_doubleSpinBox)
        
        self.settings.jog_step_z.connect_to_widget(
            self.ui.z_step_doubleSpinBox)
        
        
        self.ui.xy_stop_pushButton.clicked.connect(self.stage.halt_xy)

        self.stage.settings.speed_xy.connect_to_widget(
            self.ui.xy_speed_doubleSpinBox)

        self.stage.settings.acc_xy.connect_to_widget(
            self.ui.xy_acc_doubleSpinBox)

        self.stage.settings.backlash_xy.connect_to_widget(
            self.ui.xy_backlash_doubleSpinBox)


        ####### Buttons
        def x_up():
            self.stage.settings['x_target']+=self.settings['jog_step_xy']
        self.ui.x_up_pushButton.clicked.connect(x_up)
        
        def x_down():
            self.stage.settings['x_target']-=self.settings['jog_step_xy']
        self.ui.x_down_pushButton.clicked.connect(x_down)

        def y_up():
            self.stage.settings['y_target']+=self.settings['jog_step_xy']
        self.ui.y_up_pushButton.clicked.connect(y_up)
        
        def y_down():
            self.stage.settings['y_target']-=self.settings['jog_step_xy']
        self.ui.y_down_pushButton.clicked.connect(y_down)
        
        
        def z_up():
            self.stage.settings['z_target']+=self.settings['jog_step_z']
        self.ui.z_up_pushButton.clicked.connect(z_up)
        
        def z_down():
            self.stage.settings['z_target']-=self.settings['jog_step_z']
        self.ui.z_down_pushButton.clicked.connect(z_down)
        
        
        