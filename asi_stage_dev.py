import serial
import time
import threading

class ASIXYStage(object):
    
    def __init__(self, port='COM5', debug=False):
        self.port = port
        self.debug = debug
        self.ser = serial.Serial(port=self.port,
                         baudrate=115200,
                         # waiting time for response [s]
                         timeout=0.02,
                         bytesize=8, parity='N', 
                         stopbits=1, xonxoff=0, rtscts=0)

        self.ser.write(b'\b') # <del>  or  <bs>- Abort current command and flush input buffer
        #self.ser.flush() # flush output buffer
        self.ser.read(100)
        
        # Stage Info:
        # lead screw pitch: 6.35mm
        # achievable speed: 7mm/s
        # encoder resolution: 22nm
        
        self.unit_scale = 1e4 # convert internal units 1/10um to mm

        # threading lock
        self.lock = threading.Lock()
        
    def close(self):
        self.ser.close()
        
    def send_cmd(self, cmd):
        cmd_bytes = (cmd + '\r').encode()
        if self.debug: print("ASI XY cmd:", repr(cmd), repr(cmd_bytes))
        self.ser.write(cmd_bytes)
        if self.debug: print ("ASI XY done sending cmd")
    
    def info(self,axis):
        with self.lock:
            self.send_cmd("2HI "+axis)
            time.sleep(0.010)
            resp1 = self.ser.readline().decode()+" "
            if self.debug: print("ASI XY ask resp1:", repr(resp1))
            #read until end-of-text is received
            t0 = time.time()
            timeout = 10
            resp = 'output:\n '
            while True:
                resp2 = self.ser.readline()
                if self.debug: print("ASI XY ask resp2:", repr(resp2))
                if resp2 == b'\x03':
                    break
                resp2 = resp2.decode()+" "
                resp = resp+resp2
                if time.time()-t0 > timeout:
                    raise IOError("ASI stage took too long too respond")
        return resp
    
    def ask(self, cmd): # format: '2HW X' -> ':A 355'
        with self.lock:
            self.send_cmd(cmd)
            time.sleep(0.020)
            resp1 = self.ser.readline()
            if self.debug: print("ASI XY ask resp1:", repr(resp1))
            #read until end-of-text is received
            t0 = time.time()
            timeout = 1
            while True:
                resp2 = self.ser.readline()
                if self.debug: print("ASI XY ask resp2:", repr(resp2))
                if resp2 == b'\x03':
                    break
                if time.time()-t0 > timeout:
                    raise IOError("ASI stage took too long too respond")

        
        assert resp2 == b'\x03' # End of text (Escape sequence)
        
        resp1 = resp1.decode()
        
        assert resp1.startswith(":A")
        
        if resp1.startswith(":AERR0"):
            print("ASI-stage communication error: ERR0")
        else:
            return resp1[2:].strip() # remove whitespace


    def read_pos_x(self):
        x = self.ask("2HW X")
        return float(x)/self.unit_scale
    
    def read_pos_y(self):
        y = self.ask("2HW Y")
        return float(y)/self.unit_scale
    
    def read_pos_z(self):
        z = self.ask("1HW Z")
        return float(z)/self.unit_scale
    
    def is_busy_xy(self):
        with self.lock:
            self.send_cmd("2H/")  # status command has a different reply structure
            resp1 = self.ser.readline().decode()
            resp2 = self.ser.read(1)
        if self.debug: print("ASI isBusy resp1", repr(resp1))
        if self.debug: print("ASI isBusy resp2", repr(resp2))
        assert resp1[0] in 'NB'
        
        if resp1[0]=='N':   return False
        elif resp1[0]=='B': return True
    
    def is_busy_z(self):
        with self.lock:
            self.send_cmd("1H/")  # status command has a different reply structure
            resp1 = self.ser.readline().decode()
            resp2 = self.ser.read(1)
        assert resp1[0] in 'NB'
        
        if resp1[0]=='N':   return False
        elif resp1[0]=='B': return True
    

    def wait_until_not_busy_xy(self, timeout=10):    
        t0 = time.time()
        while self.is_busy_xy():
            time.sleep(0.020)
            if time.time() - t0 > timeout:
                raise IOError("ASI stage took too long during wait")

    def wait_until_not_busy_z(self, timeout=10):    
        t0 = time.time()
        while self.is_busy_z():
            time.sleep(0.020)
            if time.time() - t0 > timeout:
                raise IOError("ASI stage took too long during wait")

            
    def move_x(self, target):
        self.ask("2HM X= {:d}".format(self._scale(target)))
            
    def move_y(self, target):
        self.ask("2HM Y= {:d}".format(self._scale(target)))
        
    def move_z(self, target):
        self.ask("1HM Z= {:d}".format(self._scale(target)))
          
    def move_x_and_wait(self, target,timeout=10):
        if int(self.read_pos_x()*self.unit_scale) == int(target*self.unit_scale):
            return # avoid overriding with same value 
        self.move_x(target)
        self.wait_until_not_busy_xy(timeout)

    def move_y_and_wait(self, target,timeout=10):
        if int(self.read_pos_y()*self.unit_scale) == int(target*self.unit_scale):
            return # avoid overriding with same value 
        self.move_y(target)
        self.wait_until_not_busy_xy(timeout)

    def home_xy(self):
        self.ask("2HHOME X Y")
        
    def home_and_wait_xy(self, timeout=90):
        self.home_xy()
        self.wait_until_not_busy_xy(timeout)

    def home_and_wait_z(self, timeout=90):
        self.home_z()
        self.wait_until_not_busy_z(timeout)

    def set_here_z(self, target):
        self.ask("1HHERE Z= {:d}".format(self._scale(target)))
    
    def home_z(self):
        self.ask("1HHOME Z")
        
    def home_and_center_xy(self):
        speed = min(self.get_speed_x(), self.get_speed_y())
        timeout = 50./speed
        self.home_and_wait_xy(2*timeout)
        self.move_x_rel(-45)
        self.move_y_rel(-45)
        self.wait_until_not_busy_xy(timeout)
        self.zero_xy()

    def home_and_center_z(self):
        speed =self.get_speed_z()
        timeout = 30./speed
        self.home_and_wait_z(2*timeout)
        self.move_z_rel(-25)
        self.wait_until_not_busy_z(timeout)
        self.zero_z()
        
    def halt_xy(self):
        self.ask("2HHALT")
        
    def halt_z(self):
        self.ask("1HHALT")
        
    def set_limits_xy(self, xl, xu, yl, yu): # x in [xl, xu], y in [yl, yu]
        self.ask("2HSL X= {:f} Y= {:f}".format(xl, yl))
        self.ask("2HSU X=" + str(xu) + " Y=" + str(yu))
        
    def move_x_rel(self, step):
        if step!=0:
            self.ask("2HR X={:d}".format(int(step*self.unit_scale)))

    def move_y_rel(self, step):
        if step!=0:
            self.ask("2HR Y={:d}".format(int(step*self.unit_scale)))

    def set_backlash_xy(self, backlash_x, backlash_y=None):
        if backlash_y is None:
            backlash_y = backlash_x
        
        """
        set the amount of distance in millimeters to travel to
        absorb the backlash in the axis' gearing. This backlash value works with an antibacklash
        routine built into the controller. The routine ensures that the controller
        always approaches the final target from the same direction. A value of zero (0)
        disables the anti-backlash algorithm for that axis
        """
        self.ask("2HB X= {:1.4f} Y= {:1.4f}".format(backlash_x,backlash_y))
        
    def set_backlash_z(self, backlash_z):
        self.ask("1HB Z= {:1.4f}".format(backlash_z))
    
    def move_z_rel(self, step):
        if step!=0:
            self.ask("1HR Z={:d}".format(int(step*self.unit_scale)))

        
#     def get_speed_xy(self):
#         print(self.ask("2HSPEED X? Y?"))
#     

    def get_speed_x(self):
        speed = float(self.ask("2HSPEED X?").split("=")[1])
        return speed
    
    def get_speed_y(self):
        speed = float(self.ask("2HSPEED Y?").split("=")[1])
        return speed  
    
    def get_speed_z(self):
        speed = float(self.ask("1HSPEED Z?").split("=")[1])
        return speed  
        
    def set_speed_xy(self, speed_x, speed_y=None):
        if speed_y is None:
            speed_y = speed_x
        """
        Sets the maximum speed at which the stage will move. Speed is set in millimeters
        per second. Maximum speed is = 7.5 mm/s for standard 6.5 mm pitch leadscrews.
        """
        self.ask("2HSPEED X= {:1.4f} Y= {:1.4f}".format(speed_x,speed_y))
        
    def set_acc_xy(self, acc_x, acc_y=None):
        if acc_y is None:
            acc_y = acc_x
        """
        This command sets the amount of time in milliseconds that it takes an axis motor
        speed to go from the start velocity to the maximum velocity and then back down
        again at the end of the move. At a minimum, this acceleration / deceleration time
        must be greater than t_step (the amount of time it takes for the controller to go
        through one loop of its main execution code. Use the INFO command to
        determine the t_step).
        """
        self.ask("2HAC X= {:1.4f} Y= {:1.4f}".format(acc_x,acc_y))    
        
    def _scale(self, val):
        """returns integer value for built-in 
        scale from physical units (val)"""
        
        scale_int = int(val*self.unit_scale)
        # stage bug: positions can't end in 3
        if abs(scale_int) % 10 == 3: # -3 mod 10 = 7!!!
            scale_int +=1
        return scale_int
    
    def zero_xy(self):
        self.ask("2HZERO")
    def zero_z(self):
        self.ask("1HZERO")
    #### z-stage
        
    