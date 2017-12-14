import serial
import time
import re

class GrblDriver:
    """Class for interfacing with GRBL loaded on an Arduino Uno.Arduino

    Makes controlling each of the four available motors easy in terms of actual steps.
    Converting steps to mm or deg can be done on the user-side application.

    NOTE: GRBL config.h had to be modified in order to make GRBL v1.1 compatible
    with the arduino shield (https://blog.protoneer.co.nz/arduino-cnc-shield/).
    Pin D12 is by default used for spindle control.  Comment the line (line339)
    to disable spindle control so that z-limit switch is on the right pin.

    HOMING: GRBL config.h was also modified on lines 106, 124, and 129.
    106: disable xy homing after z for G28 command (don't need this with single axis homing)
    124: enable single axis homing commands, $HX,$HY,$HZ
    129: homing force set origin, coordinates are zeroed after homing 
            (as opposed to negative for professional CNC machines)
    """
    
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM0',baudrate=115200,timeout=0.01)
        self.waittimeout = 0.01

        #initialize and wait for grbl to wake up
        self._write('\r\n\r\n')
        time.sleep(2)
        self.ser.reset_input_buffer()

        # x-motor configuration
        self.xconfig = {
            'steps/sec':6400, #<--the actual important parameter
            'steps/sec2':5000, #<--acceleration
            'steps/mm':1000 #<--sets resolution, chosen so that 0.001mm = 1 step, the minimum resolution of GRBL
            }
        
        #map x settings to grbl commands
        self.xsettingsmap = {
            'steps/mm':'$100',
            'mm/min':'$110', #max rate, not constant speed
            'mm/sec2':'$120' #accel
        }

        # y-motor configuration
        self.yconfig = {
            'steps/sec':6400, #<--the actual important parameter
            'steps/sec2':5000, #<--acceleration
            'steps/mm':1000 #<--sets resolution, chosen so that 0.001mm = 1 step, the minimum resolution of GRBL
            }
        
        #map y settings to grbl commands
        self.ysettingsmap = {
            'steps/mm':'$101',
            'mm/min':'$111', #max rate, not constant speed
            'mm/sec2':'$121' #accel
        }
        
        # Z-motor configuration
        self.zconfig = {
            'steps/sec':6400, #<--the actual important parameter
            'steps/sec2':5000, #<--acceleration
            'steps/mm':1000 #<--sets resolution, chosen so that 0.001mm = 1 step, the minimum resolution of GRBL
            }
        
        #map z settings to grbl commands
        self.zsettingsmap = {
            'steps/mm':'$102',
            'mm/min':'$112', #max rate, not constant speed
            'mm/sec2':'$122' #accel
        }

        #internal, to write to fit into grbl's interface
        self._update_writesettings()

        self.globalconfig = {
            1:255, #ms to wait before going idle (255=don't disable steppers)
            5:1,  #set NC limit switch
            21:1, # enable hard limit switch (stop immediately)
            22:1, # enable homing cycle
            24:25, # homing speed 
            25:300 # homing speed

        }
        
    def _update_writesettings(self):
        self.xwritesettings={
            'steps/mm':1000,
            'mm/min':self.xconfig['steps/sec']/self.xconfig['steps/mm']*60,
            'mm/sec2':self.xconfig['steps/sec2']/self.xconfig['steps/mm']
        }
        self.ywritesettings={
            'steps/mm':1000,
            'mm/min':self.yconfig['steps/sec']/self.yconfig['steps/mm']*60,
            'mm/sec2':self.yconfig['steps/sec2']/self.yconfig['steps/mm']
        }
        self.zwritesettings={
            'steps/mm':1000,
            'mm/min':self.zconfig['steps/sec']/self.zconfig['steps/mm']*60,
            'mm/sec2':self.zconfig['steps/sec2']/self.zconfig['steps/mm']
        }

    def write_global_config(self, wait=0.5):
        """Should only need to be run at initial setup.  Configures
        global options like homing speed, limit switch behavior."""
        self.ser.reset_input_buffer()
        for k,v in self.globalconfig.items():
            self._write('${}={}'.format(k,v))
            time.sleep(wait) #longer wait time to write to EEPROM
        resp = self._read_buffer()
        for r in resp:
            assert r == 'ok','Ok not received after attempted write.'
        
    def _write_settings(self, settings, settingsmap, wait=0.5):
        """Utility function to write motor config settings to GRBL"""
        #TODO: make this only write commands that have changed,
        #to save on the number of writes to EEPROM
        self.ser.reset_input_buffer()
        for s, v in settings.items():
            self._write(settingsmap[s]+'={:.3f}'.format(v))
            time.sleep(wait) #longer wait time to write to EEPROM
        resp = self._read_buffer()
        for r in resp:
            assert r == 'ok','Ok not received after attempted write.'

    def write_all_settings(self):
        """Write settings for all of the motors to GRBL"""
        self._update_writesettings()
        maps = (self.xsettingsmap, self.ysettingsmap, self.zsettingsmap)
        writemaps = (self.xwritesettings, self.ywritesettings, self.zwritesettings)
        for settingsmap, setting in zip(maps, writemaps):
            self._write_settings(setting, settingsmap)

    def verify_settings(self):
        """Verify that current GRBL settings match the desired config of this class"""
        settingsre = re.compile(r'(\$\d{1,3})=(\d{1,5}\.?\d{0,3})')
        
        self.ser.reset_input_buffer()
        
        self._write('$$')
        time.sleep(self.waittimeout)
        resp = self._read_buffer()
        maps = (self.xsettingsmap, self.ysettingsmap, self.zsettingsmap)
        writemaps = (self.xwritesettings, self.ywritesettings, self.zwritesettings)
        for settingsmap, checksettings in zip(maps, writemaps):
            # read settings specified in settingsmap
            settings = {}
            for s in resp:
                m = settingsre.match(s)
                if m is not None:
                    cmd, reading = m.groups()
                    for k, v in settingsmap.items():
                        if cmd == v:
                            settings[k] = float(reading)
                            
            # compare to checksettings to verify:
            for s, v in checksettings.items():
                if settings[s] != checksettings[s]:
                    raise Exception(
                        ('Current setting for {} is {}, but {} is expected.'
                         ' Consider writing the settings again.'
                        ).format(s,v,settings[s]))

        #verify global config
        for s in resp:
            m = re.match(r'\$(\d*)=(\d*\.?\d*)',s)
            if m is not None:
                cmd, reading = m.groups()
                cmd = int(cmd)
                reading = float(reading)
                if cmd in self.globalconfig.keys():
                    if reading != self.globalconfig[cmd]:
                        raise Exception(('Current setting for global config ${} is {},'
                            'but {} is expected.').format(cmd,self.globalconfig[cmd],reading))

        
        return True
        
    def _write(self, command):
        """Utility function, write string to GRBL"""
        self.ser.write(command.encode('ascii')+b'\r')
    
    def _read_buffer(self, maxreads = 100):
        """Utility function, perform readlines into a list of readings
        from GRBL.  Useful to clear the read buffer."""
        resp = []
        i = 0
        while i < maxreads:
            msg = self.ser.readline()
            if msg == b'':
                break
            resp.append(msg.decode().strip())
            time.sleep(self.waittimeout)
            i+=1
        return resp
    
    def _move(self, axis, steps, config, blocking = True, pingwait = 0.25):
        """Move axis with optional blocking"""
        pos = steps/config['steps/mm']
        self._write('G90')
        self._write('G0 '+axis+str(pos))
        if blocking:
            time.sleep(self.waittimeout)
            while self.get_status_report()[0] == 'Run':
                time.sleep(pingwait)
            currentsteps = self.get_positions()[axis]
            assert currentsteps - steps < 1, 'Didn\'t get there! Stopped at {} even though {} was requested.'.format(currentsteps,steps)
        
    def xmove(self, steps, blocking = True):
        """Move x-axis motor by requested number of steps"""
        self._move('X', steps, self.xconfig, blocking=blocking)

    def ymove(self, steps, blocking = True):
        """Move y-axis motor by requested number of steps"""
        self._move('Y', steps, self.yconfig, blocking=blocking)

    def zmove(self, steps, blocking = True):
        """Move z-axis motor by requested number of steps"""
        self._move('Z', steps, self.zconfig, blocking=blocking)

    def zhome(self):
        """Run the homing cycle for the z-axis"""
        self._write('$HZ')

    def get_status_report(self):
        """Retrieve and parse GRBL status report"""
        self.check_alarm(self._read_buffer())
        self._write('?')
        time.sleep(self.waittimeout)
        resp = self._read_buffer()
        self.check_alarm(resp)
        
        assert re.match(r'\<.*\>',resp[0]) is not None, 'Error reading status report'
        resp = resp[0].strip('<>').split('|')
        state = resp.pop(0)
        status = {}
        for r in resp:
            s, v = re.match(r'(.*):(.*)',r).groups()
            status[s] = v
        return state, status
    
    def check_alarm(self, bufferoutput):
        for m in bufferoutput:
            if m.split(':')[0] == 'ALARM':
                raise Exception(('Alarm status! Probably hit a hard limit!'
                                'Perform soft_reset and alarm_reset to reset operation.'))

    def get_positions(self):
        """Request status and return positions in a dict"""
        state, status = self.get_status_report()
        posre = re.compile(r'(-?\d*\.\d*),(-?\d*\.\d*),(-?\d*\.\d*)')
        positions = [float(x) for x in posre.match(status['MPos']).groups()]
        configs = (self.xconfig,self.yconfig,self.zconfig)
        steppositions = []
        for p, c in zip(positions, configs):
            steppositions.append(p*c['steps/mm'])
        keys = ['X','Y','Z']
        return dict(zip(keys,steppositions))

    def _human_readable_settings(self):
        """Utility function to read all GRBL settings that attempts to load
        csv file containing settings descriptions."""
        settingsre = re.compile(r'\$(\d{1,3})=(\d{1,5}\.?\d{0,3})')

        self.ser.reset_input_buffer()

        self._write('$$')
        time.sleep(self.waittimeout)
        resp = self._read_buffer()
        
        current = []
        for s in resp:
            m = settingsre.match(s)
            if m is not None:
                cmd, reading = m.groups()
                current.append([int(cmd), float(reading)])
                
        currentdf = pd.DataFrame(current,columns=['$-Code','Value'])
        
        try:
            settings_descriptions = pd.read_csv('C:/Users/Lab X-ray/Downloads/grbl_setting_codes_en_US.csv')
            currentdf = pd.merge(currentdf,settings_descriptions,on='$-Code')
        except OSError:
            print('Settings descriptions file not found, returning settings without descriptions.')
        
        return currentdf

    def soft_reset(self):
        """Perform soft-reset of GRBL.  Doesn't lose motor positions"""
        self._write('\x18')
        time.sleep(self.waittimeout)
        self._read_buffer()
        
    def controlled_stop(self, pingwait=0.25):
        """Perform stop with controlled deceleration to maintain motor positioning."""
        self._write('!')
        time.sleep(pingwait)
        while True:
            state,_=self.get_status_report()
            if state.split(':')[1] == '0':
                break
            time.sleep(pingwait)
        time.sleep(pingwait)
        self.soft_reset()

    def stop(self):
        """Emergency stop that stops all motion. Loses motor positioning."""
        self.soft_reset()

    def alarm_reset(self):
        """Reset 'alarm' status, usually after emergency stop or hard limit."""
        self._write('$X')

    def close(self):
        """Close GRBL serial connection"""
        self.ser.close()