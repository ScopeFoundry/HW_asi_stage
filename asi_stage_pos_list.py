from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
from collections import OrderedDict
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFileDialog
import time
import csv
import os


class ASIStagePositionList(Measurement):
    name = "asi_stage_position_list"
    
    def setup(self):
        self.stage = self.app.hardware['asi_stage']
        
        self.ui_filename = sibling_path(__file__,"asi_position_list.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        self.display_update_period = 0.5 # seconds
        
        self.locations = OrderedDict()
        
        S = self.settings
        S.New('loc_name', dtype=str, ro=False)
        S.New('loc_x', dtype=float, ro=True, spinbox_decimals=4, unit='mm')
        S.New('loc_y', dtype=float, ro=True, spinbox_decimals=4, unit='mm')
        S.New('loc_z', dtype=float, ro=True, spinbox_decimals=4, unit='mm')
        
        self.add_operation('go to saved pos', self.go_to_position)
        self.add_operation('go to prev pos', self.go_to_previous)
        self.add_operation('halt stage', self.halt_stage)
        self.add_operation('save current pos', self.save_position)
        self.add_operation('load saved pos', self.load_position)
        self.add_operation('save previous position', self.save_previous)
        self.add_operation('delete position', self.delete_position)
        
    def setup_figure(self):
        S = self.settings
        
        S.loc_name.connect_to_widget(self.ui.position_name_lineEdit)
        
        S.loc_x.connect_to_widget(self.ui.saved_x_doubleSpinBox)
        S.loc_y.connect_to_widget(self.ui.saved_y_doubleSpinBox)
        S.loc_z.connect_to_widget(self.ui.saved_z_doubleSpinBox)
        
        self.stage.settings.x_position.connect_to_widget(self.ui.x_doubleSpinBox)
        self.stage.settings.y_position.connect_to_widget(self.ui.y_doubleSpinBox)
        self.stage.settings.z_position.connect_to_widget(self.ui.z_doubleSpinBox)
        
        self.ui.save_pushButton.clicked.connect(self.save_position)
        self.ui.halt_pushButton.clicked.connect(self.halt_stage)
        self.ui.go_pushButton.clicked.connect(self.go_to_position)
        self.ui.go_pushButton.clicked.connect(self.save_previous)
        self.ui.previous_pushButton.clicked.connect(self.go_to_previous)
        self.ui.previous_pushButton.clicked.connect(self.save_previous)
        self.ui.delete_pushButton.clicked.connect(self.delete_position)
        
        self.ui.load_file_pushButton.clicked.connect(self.load_list)
        self.ui.save_file_pushButton.clicked.connect(self.save_list)
        
        self.list = self.ui.position_listWidget
        self.list.itemSelectionChanged.connect(self.load_position)
    
    def load_position(self, item=None):
        item = self.list.currentItem()
        loc = self.locations[item.text()]
        self.settings.loc_name.update_value(item.text())
        self.settings.loc_x.update_value(loc[0])
        self.settings.loc_y.update_value(loc[1])
        self.settings.loc_z.update_value(loc[2])
        
    def delete_position(self):
        item = self.list.currentItem()
        self.delete_loc(item.text())
    
    def halt_stage(self):
        self.stage.halt_xy()
        self.stage.halt_z()
        
    def add_loc(self, name):
        if name not in list(self.locations.keys()):
            self.list.addItem(name)
        self.locations[name] = (self.stage.settings['x_position'],
                                self.stage.settings['y_position'],
                                self.stage.settings['z_position'])
    
    def delete_loc(self, name):
        # self.list.removeItemWidget(items[0]) # doesn't work for some reason...
        for kk in range(len(self.locations)):
            if self.list.item(kk).text() == name:
                self.list.takeItem(kk)
                self.locations.pop(name)
                return
    
    def save_previous(self):
        if self.stage.settings['connected']:
                self.add_loc('previous')
    
    def save_position(self):
        if self.stage.settings['connected']:
            self.add_loc(self.settings.loc_name.val)
    
    def go_to_position(self):
        if self.stage.settings['connected']:
            self.stage.move_x(self.settings.loc_x.val)
            self.stage.move_y(self.settings.loc_y.val)
            self.stage.move_z(self.settings.loc_z.val)
            
            while self.stage.is_busy_xy() or self.stage.is_busy_z():
                time.sleep(0.1)
            
    def go_to_previous(self):
        items = self.list.findItems('previous', Qt.MatchExactly)
        self.list.setCurrentItem(items[0])
        self.location_selected(items[0])
        self.go_to_position()
        
    def save_list(self):
        t = time.localtime(time.time())
        t_string = "{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(int(str(t[0])[2:4]), t[1], t[2], t[3], t[4], t[5])
        fname = os.path.join(self.app.settings['save_dir'], "%s_%s" % (t_string, self.name))
        
        with open(fname+'.csv', 'w', newline='') as listfile:
            print('Saving position list to %s.csv' % fname)
            w = csv.writer(listfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            w.writerow(['Location name', 'x (mm)', 'y (mm)', 'z (mm)'])
            for key, val in self.locations.items():
                print(key, val)
                if key != 'previous':
                    w.writerow([key, val[0], val[1], val[2]])
        
    def load_list(self):
        fname = QFileDialog.getOpenFileName(None, "Select location file...", self.app.settings['save_dir'], filter='csv (*.csv)')
        if len(fname[0]) > 0:
            with open(fname[0], newline='') as listfile:
                print('Loading position list from ' + fname[0])
                r = csv.reader(listfile, delimiter='\t')
                for row in r:
                    print(row[0])
                    if row[0] != 'Location name':
                        if row[0] not in list(self.locations.keys()):
                            self.list.addItem(row[0])
                        self.locations[row[0]] = (float(row[1]), float(row[2]), float(row[3]))
    