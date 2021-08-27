from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
from pyqtgraph.widgets.ComboBox import ComboBox

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


        self.ui.x_target_lineEdit.returnPressed.connect(
            self.stage.settings.x_target.update_value)
        self.ui.x_target_lineEdit.returnPressed.connect(
            lambda: self.ui.x_target_lineEdit.setText(""))
        self.ui.y_target_lineEdit.returnPressed.connect(
            self.stage.settings.y_target.update_value)
        self.ui.y_target_lineEdit.returnPressed.connect(
            lambda: self.ui.y_target_lineEdit.setText(""))
        self.ui.z_target_lineEdit.returnPressed.connect(
            self.stage.settings.z_target.update_value)
        self.ui.z_target_lineEdit.returnPressed.connect(
            lambda: self.ui.z_target_lineEdit.setText(""))
        
        self.settings.jog_step_xy.connect_to_widget(
            self.ui.xy_step_doubleSpinBox)
        
        self.settings.jog_step_z.connect_to_widget(
            self.ui.z_step_doubleSpinBox)
        
        
        self.ui.xy_stop_pushButton.clicked.connect(self.stage.halt_xy)
        self.ui.home_xy_pushButton.clicked.connect(self.stage.home_xy)

        self.ui.z_stop_pushButton.clicked.connect(self.stage.halt_z)
        self.ui.home_z_pushButton.clicked.connect(self.stage.home_z)

        self.stage.settings.acc_xy.connect_to_widget(
            self.ui.acc_xy_doubleSpinBox)
        
        self.stage.settings.speed_xy.connect_to_widget(
            self.ui.speed_xy_doubleSpinBox)
        
        self.stage.settings.backlash_xy.connect_to_widget(
            self.ui.backlash_xy_doubleSpinBox)
        
        speedDict = {'fast':1.00, 'slow':0.001}
        self.ui.speed_z_comboBox.addItems(speedDict)
        def set_z_speed():
            self.stage.settings['speed_z'] = speedDict.get(self.ui.speed_z_comboBox.currentText())
        self.ui.speed_z_comboBox.currentIndexChanged.connect(set_z_speed)
        
        
        ####### Buttons

        self.ui.x_up_pushButton.clicked.connect(self.x_up)
        
        self.ui.x_down_pushButton.clicked.connect(self.x_down)

        self.ui.y_up_pushButton.clicked.connect(self.y_up)
        
        self.ui.y_down_pushButton.clicked.connect(self.y_down)
        
        self.ui.z_up_pushButton.clicked.connect(self.z_up)
        self.ui.z_down_pushButton.clicked.connect(self.z_down)
        
        
        
        

    def x_up(self):
        self.stage.settings['x_target']+=self.settings['jog_step_xy']
        #self.stage.move_x_rel(self.settings['jog_step_xy'])
    
    def x_down(self):
        #self.stage.move_x_rel(-self.settings['jog_step_xy'])
        self.stage.settings['x_target']-=self.settings['jog_step_xy']


    def y_up(self):
        self.stage.settings['y_target']+=self.settings['jog_step_xy']
        #self.stage.move_y_rel(self.settings['jog_step_xy'])

    
    def y_down(self):
        self.stage.settings['y_target']-=self.settings['jog_step_xy']
        #self.stage.move_y_rel(-self.settings['jog_step_xy'])

    
    def z_up(self):
        #self.stage.move_z_rel(self.settings['jog_step_z'])
        self.stage.settings['z_target']+=self.settings['jog_step_z']
    
    def z_down(self):
        #self.stage.move_z_rel(-self.settings['jog_step_z'])
        self.stage.settings['z_target']-=self.settings['jog_step_z']
