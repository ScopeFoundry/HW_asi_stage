'''
Created on Sep 25, 2014

@author:  DZiegler  dominik@scubaprobe.com 

Updated 2018 by Edward Barnard esbarnard@lbl.gov

Serial communication with the controller of the motorized ASI xy-stage. 

'''
import serial
import time


class ASIXYStage(object):
    def __init__(self, port='COM4', debug=False):
        self.port = port
        
        self.debug = debug
        self.waitTime = 0.1
        
        if self.debug: print("ASI XY Stage Initialization")
        self.ser = serial.Serial(port=self.port,
                                 baudrate=115200,
                                 # waiting time for response [s]
                                 timeout=0.1,
                                 bytesize=8, parity='N', 
                                 stopbits=1, xonxoff=0, rtscts=0)
        self.ser.write(b'\b') # <del>  or  <bs>- Abort current command and flush input buffer
        self.ser.flush() # flush output buffer
        #time.sleep(0.1)
        
        # Stage Info:
        # lead screw pitch: 6.35mm
        # achievable speed: 7mm/s
        # encoder resolution: 22nm
        
        # set the coordinate frame
        self.unitMultiplier = 10 # converts the unit used to tenths of microns
        self.c_mm = 10**4 / self.unitMultiplier    # conversion to mm
#         if __name__ == '__main__':
#             f = open('ASIStageCurrentPosition.txt','r')
#         else:
#             f = open('equipment/ASIStageCurrentPosition.txt','r')
#         storedPos = f.read().split("\t")
#         
#         self.setCurrentPosToXY(float(storedPos[0]), float(storedPos[1]), float(storedPos[2]))
#         f.close()
        
        """# configure stage
        self.setLimits(-50, 50, -50, 50)    # travel range [mm]
        self.setLimitsZ(-10, 5)                # travel range in mm (-10, 5)
        self.setDriftErrorXY(0.01, 0.01)    # drift error [mm]
        self.setFinishErrorXY(0.02, 0.02)    # finish error [mm]
        # maximum speed [mm/s]
        self.v_max_x = 7
        self.v_max_y = 7
        self.v_max_z = 7
        self.setMaxSpeedXY(self.v_max_x, self.v_max_y)
        self.setMaxSpeedZ(self.v_max_z)
        # ramp time [ms]
        self.t_ramp_x = 50
        self.t_ramp_y = 50
        self.setRampTimeXY(self.t_ramp_x, self.t_ramp_y)
        
        self.setBacklashXY(0, 0)    # anti backlash movement [mm]
        self.setBacklashZ(0)
         
                 
        # close laser shutter
        self.moveFWto(5)
        """
        
        
    def send_cmd(self, cmd):
        if self.debug: print(("ASI XY cmd:", repr(cmd)))
        self.ser.write((cmd + '\r').encode())
        if self.debug: print ("ASI XY done sending cmd")
        
    def ask(self, cmd): # format: '2HW X' -> ':A 355'
        self.send_cmd(cmd)
        resp1 = self.ser.readline()
        #time.sleep(0.1) #test Dominik 
        if self.debug: print("ASI XY ask resp1:", repr(resp1))
        resp2 = self.ser.read(1)
        if self.debug: print("ASI XY ask resp2:", repr(resp2))
        
        # error handling
        if not resp2 == b'\x03': # End of text (Escape sequence)
            print("Missing End of Text")
            
        resp1 = resp1.decode()
        if not resp1.startswith(":A"):
            print("ASI-stage communication error: missing ':A' ")
            print("resp1 is ", resp1)
            print("resp2 is ", resp2) 
        if resp1.startswith(":AERR0"):
            print("ASI-stage communication error: ERR0")
        else:
            return resp1[2:].strip() # remove whitespace

    def askFW(self, cmd): # format: '2HW X' -> ':A 355'
        self.send_cmd(cmd)
        resp1 = self.ser.readline().decode()
        if self.debug: print("ASI XY ask resp1:", repr(resp1))
        resp2 = self.ser.read(1)
        if self.debug: print("ASI XY ask resp2:", repr(resp2))
        
        # error handling
        if resp1.startswith("ERR0"):
            print("ASI-stage communication error: ERR0")
        else:
            return resp1[2:].strip() #s remove whitespace

    def getPosX(self):
        try:
            posx=self.ask("2HW X")
            posx=float(posx)/float(self.unitMultiplier)
            return float(posx)
        except:
            print('could not read x position')
            return float(0.0)
            return
    
    def getPosY(self):
        try: 
            posy=self.ask("2HW Y")
            posy=float(posy)/float(self.unitMultiplier)
            return float(posy)
        except:
            print('could not read y position')
            return float(0.0)
            return 
        
    def getPosZ(self):
        try: 
            posz=self.ask("1HW Z")
            posz=float(posz)/float(self.unitMultiplier)
            return float(posz)
        except:
            print('could not read z position')
        
    def getPosXY(self):
        return (self.getPosX(), self.getPosY())
    
    def isBusy(self):
        if self.debug: print("motors busy?")
        self.send_cmd("2H/")  # status command has a different reply structure
        resp1 = self.ser.readline().decode()
        resp2 = self.ser.read(1)
        if self.debug: print("ASI isBusy resp1", repr(resp1))
        if self.debug: print("ASI isBusy resp2", repr(resp2))
        if resp1[0]=='N': return False
        elif resp1[0]=='B': return True
        else:
            # Communication Error: Wait for move to be completed
            sleepTime = 1 # [s]
            print("Incomprehensible answer to isBusy() command. Sleep for %d s." %sleepTime)
            time.sleep(sleepTime)
            return False
        
    def isZBusy(self):
        if self.debug: print("motors busy?")
        self.send_cmd("1H/")  # status command has a different reply structure
        resp1 = self.ser.readline()
        resp2 = self.ser.read(1)
        if self.debug: print("ASI isBusy resp1", repr(resp1))
        if self.debug: print("ASI isBusy resp2", repr(resp2))
        if resp1[0]=='N': return False
        elif resp1[0]=='B': return True
        else:
            # Communication Error: Wait for move to be completed
            sleepTime = 7 # [s]
            print("Incomprehensible answer to isZBusy() command. Sleep for %d s." %sleepTime)
            time.sleep(sleepTime)
            
            if __name__ == '__main__':
                f = open('ASIStageErrorPosition.txt','a')
            else:
                f = open('equipment/ASIStageErrorPosition.txt','a')
            f.write("bla" + "\n")
            f.close()
            return False
        
    def isFWBusy(self):
        if self.debug: print("FW busy?")
        self.send_cmd("3FDE")  # DumpsErrors
        resp1 = self.ser.readline().decode()
        resp2 = self.ser.read(1)
        if self.debug: print("ASI isBusy resp1", repr(resp1))
        if self.debug: print("ASI isBusy resp2", repr(resp2))
        return False
        
        
    def wait(self):
        if self.debug: print("wait")
        while self.isBusy():
            time.sleep(self.waitTime)
                
                
    def waitZ(self):
        if self.debug: print("wait")
        while self.isZBusy():
            time.sleep(self.waitTime)
    
    def waitFW(self):
        if self.debug: print("wait")
        while self.isFWBusy():
            time.sleep(self.waitTime)
                
    def moveToX(self, target):
        x_int = self.workaroundASIStageBug(target)
        measPosX_int = int(self.getPosX()*self.unitMultiplier)
        if x_int != measPosX_int:  # avoid overriding with same value 
            self.ask("2HM X= {:d}".format(x_int))
            self.wait()
            #self.writePosToFile()
        
    def moveToY(self, target):
        y_int = self.workaroundASIStageBug(target)
        measPosY_int = int(self.getPosY()*self.unitMultiplier)
        if y_int != measPosY_int:  # avoid overriding with same value 
            self.ask("2HM Y= {:d}".format(y_int))
            self.wait()
            #self.writePosToFile()
            
    def moveToZ(self, target):
        z_int = self.workaroundASIStageBug(target)
        measPosZ_int = int(self.getPosZ()*self.unitMultiplier)
        if z_int != measPosZ_int:  # avoid overriding with same value 
            self.ask("1HM Z=" + str(z_int))
            self.waitZ()
            #self.writePosToFile()
        
    def moveToXY(self, targetX, targetY):
        (x_int, y_int) = self.workaroundASIStageBug(targetX, targetY)
        posx=float(self.getPosX())
        time.sleep(0.1)
        measPosX_int = int(posx*self.unitMultiplier)
        posy=float(self.getPosY())
        time.sleep(0.1)
        measPosY_int = int(posy*self.unitMultiplier)
        print((x_int, y_int))
        if (x_int!=measPosX_int and y_int!= measPosY_int):
            self.ask("2HM X=" + str(x_int) + " Y=" + str(y_int))
            self.wait()
            #self.writePosToFile()
        elif (x_int!=measPosX_int and y_int==measPosY_int):
            self.ask("2HM X=" + str(x_int))
            self.wait()
            #self.writePosToFile()  
        elif (x_int==measPosX_int and y_int!=measPosY_int):
            self.ask("2HM Y=" + str(y_int))
            self.wait()
            #self.writePosToFile()
        
    def moveRelX(self, step):
        if step!=0:
            step_int = self.workaroundASIStageBug(step)
            self.ask("2HR X=" + str(step_int))
            self.wait()
            self.writePosToFile()
        
    def moveRelY(self, step):
        if step!=0:
            step_int = self.workaroundASIStageBug(step)
            self.ask("2HR Y=" + str(step_int))
            self.wait()
            self.writePosToFile()
            
    def moveRelZ(self, stepZ):
        if stepZ!=0:
            stepZ_int= self.workaroundASIStageBug(stepZ)
            self.ask("1HR Z=" + str(stepZ_int))
            self.waitZ()
            #self.writePosToFile()
    
    def moveRelXY(self, stepX, stepY):
        if stepX==0 and stepY!=0:
            self.moveRelY(stepY)
        elif stepX!=0 and stepY==0:
            self.moveRelX(stepX)
        elif stepX!=0 and stepY!=0:
            stepX_int, stepY_int = self.workaroundASIStageBug(stepX, stepY)             
            self.ask("2HR X=" + str(stepX_int) + " Y=" + str(stepY_int))
            self.wait()
            #self.writePosToFile()

    def homeXY(self):
        self.ask("2HHOME X Y")
        
    
    
    def workaroundASIStageBug(self, a, *b):
        # Some positions cannot be processed by ASI stage,
        # leading to communication issues.
        # All of them end with the digit 3.
        # workaround: add a tenth of a micron
        
        #disable workaround
        if len(b) == 1:
            return int(a*self.unitMultiplier), int(b*self.unitMultiplier)
        else:
            return int(a*self.unitMultiplier)
        #work around
        a_int = int(a*self.unitMultiplier)
        if int(str(a_int)[-1]) == 3: a_int += 1
        if len(b)==1:
            b_int = int(b[0]*self.unitMultiplier)        
            if int(str(b_int)[-1]) == 3: b_int += 1
            return (a_int, b_int)
        else:
            return a_int            
            
    def writePosToFile(self):
        x = self.getPosX()
        y = self.getPosY()
        z = self.getPosZ()
        if __name__ == '__main__':
            f = open('ASIStageCurrentPosition.txt','w')
        else:
            f = open('equipment/ASIStageCurrentPosition.txt','w')
        f.write(str(x) + "\t" + str(y)+ "\t" + str(z))
        f.close()
        
    def setCurrentPosToXY(self, x, y, z):  # changes coordinate frame
        measPosX, measPosY = self.getPosXY()
        measPosZ = self.getPosZ()
        x_int = int(x*self.unitMultiplier)
        y_int = int(y*self.unitMultiplier)
        z_int = int(z*self.unitMultiplier)
        #measured positions may differ by 0.1 microns without moving
        if abs(x_int - int(measPosX*self.unitMultiplier)) > 1:  # avoid overriding with same value 
            self.ask("2HH X=" + str(x_int))
        if abs(y_int - int(measPosY*self.unitMultiplier)) > 1:  # avoid overriding with same value 
            self.ask("2HH Y=" + str(y_int))        
        if abs(z_int - int(measPosZ*self.unitMultiplier)) > 1:  # avoid overriding with same value 
            self.ask("1HH Z=" + str(z_int))        
        
    def setLimits(self, xl, xu, yl, yu): # x in [xl, xu], y in [yl, yu]
        self.ask("2HSL X=" + str(xl) + " Y=" + str(yl))
        self.ask("2HSU X=" + str(xu) + " Y=" + str(yu))
    
    def setLimitsZ(self, zl, zu): # z in [zl, zu]
        self.ask("1HSL Z=" + str(zl))
        self.ask("1HSU Z=" + str(zu))
                
    def setDriftErrorXY(self, x, y):
        self.ask("2HE X=" + str(x) + " Y=" + str(y))
    
    def setFinishErrorXY(self, x, y):
        self.ask("2HPC X=" + str(x) + " Y=" + str(y))
        
    def    setMaxSpeedXY(self, x, y):
        self.ask("2HS X=" + str(x) + " Y=" + str(y))

    def    setMaxSpeedZ(self, z):
        self.ask("1HS Z=" + str(z))
        
    def setRampTimeXY(self, x, y):
        if (x>20 and y>20): # avoid high currents
            self.ask("2HAC X=" + str(x) + " Y=" + str(y))
        else: raise ValueError("Motor ramp time too low.")        
    def setBacklashXY(self, x, y):
        self.ask("2HB X=" + str(x) + " Y=" + str(y))
    
    def setBacklashZ(self, z):
        self.ask("1HB Z=" + str(z))
        
    def moveFWto(self, filtpos):
        """ Move filter wheel to position"""
        self.askFW("3FDE") # Dumps errors 
        self.askFW("3FMP " + str(filtpos))
        self.waitFW()
        self.askFW("3FDE") # Dumps errors 
        self.askFW("1HDE") # Dumps errors    
        self.askFW("2HDE") # Dumps errors
        
    def stopASI(self):
        self.send_cmd("1H HALT")
        #self.ser.write("HALT" + '\r')
        self.ser.readline() #dump error
        self.ser.readline() #dump error
        
        self.send_cmd("2H HALT")
        self.ser.readline() #dump error
        self.ser.readline() #dump error
        self.writePosToFile()
                
        self.send_cmd("3F HALT")
        self.ser.readline() #dump error
        self.ser.readline() #dump error
    
    def close(self):
        self.ser.close()
        print('closed ASI xy-stage')
        
if __name__ == '__main__':
    stage = ASIXYStage(port="COM4", debug=False)

    stage.close()
