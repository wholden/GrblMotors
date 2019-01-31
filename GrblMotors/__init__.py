from .grbldriver import GrblDriver

motordict = {
    'camera':{
        'devname':'camera',
        'stepsperrev':200,
        'leadscrewpitch':1/40*25.4,
        'microstep':16,
        'direction':-1
        },
    'sample':{
        'devname':'sample',
        'stepsperrev':200,
        'pulleyratio':16/60,
        'microstep':16,
        'direction':1
        }
}

motordict['camera']['mmperstep'] = motordict['camera']['leadscrewpitch']/motordict['camera']['stepsperrev']/motordict['camera']['microstep']
motordict['sample']['degperstep'] = 360*motordict['sample']['pulleyratio']/motordict['sample']['stepsperrev']/motordict['sample']['microstep']

SERIAL_ADDRESS = '/dev/ttyACM0'


global motors

global ISHOMED
ISHOMED = False

def initialize():
    global motors
    motors = GrblDriver()
    motors.verify_settings()

def go_to_degree(degree, blockuntilcomplete = True):
    """Move sample motor to angular position indicated by degree.
    
    This moves the sample rotator to the indicated position.
    Current implementation sets degree=0 to location at 
    powerup of the controller. Zero location can be reset
    by sending 'PX=0' string to the controller.

    Angular position is calculated based on configuration
    in motordict dictionary.  Calculation makes use of
    'pulleyratio', 'stepsperrev', and 'microstep'.

    Args:
        degree: Degree of position to rotate to.
    """
    steps = degree/motordict['sample']['degperstep']
    steps = steps*motordict['sample']['direction']
    motors.ymove(steps, blocking = blockuntilcomplete)

def go_to_mm(distance,blockuntilcomplete = True):
    """Move camera motor to position indicated by distance(mm).
    
    This moves the camera stage to the indicated position.
    Make sure to zero the controller out by using the 'L-'
    command string, so that distance=0 is properly calibrated.

    Distance (mm) is calculated based on configuration
    in motordict dictionary.  Calculation makes use of
    'leadscrewpitch', 'stepsperrev', and 'microstep'.

    Args:
        distance: Distance in mm to move the camera to.
    """
    global ISHOMED
    if not ISHOMED:
        raise RuntimeError('Camera motor not homed yet. Home camera before moving. WATCH camera during homing.')
    steps = distance/motordict['camera']['mmperstep']
    steps = steps*motordict['camera']['direction']
    motors.zmove(steps, blocking = blockuntilcomplete)

def get_camera_position():
    return motors.get_positions()['Z']*motordict['camera']['mmperstep']*motordict['camera']['direction']

def get_sample_position():
    return motors.get_positions()['Y']*motordict['sample']['degperstep']*motordict['sample']['direction']

def home_camera():
    motors.zhome()
    global ISHOMED
    ISHOMED = True

def stop():
    motors.stop()

def controlled_stop():
    motors.controlled_stop()

def close():
    motors.close()

def reset():
    motors.soft_reset()

def clear_alarm():
    motors.alarm_reset()