

def generate(project):
    print("generating linux-cnc config")

    cfgini_data = []

    axis_names = ["X", "Y", "Z", "A", "B", "C"]
    axis_str = ""
    axis_str2 = ""
    for num in range(min(project['joints'], len(axis_names))):
        axis_str += axis_names[num]
        axis_str2 += " " + axis_names[num]


    cfgini_data.append(f"""
    # Basic LinuxCNC config for testing of Remora firmware

    [EMC]
    MACHINE = Remora-{axis_str}
    DEBUG = 0
    VERSION = 1.1

    [DISPLAY]
    DISPLAY = axis
    EDITOR = gedit
    POSITION_OFFSET = RELATIVE
    POSITION_FEEDBACK = ACTUAL
    ARCDIVISION = 64
    GRIDS = 10mm 20mm 50mm 100mm
    MAX_FEED_OVERRIDE = 1.2
    MIN_SPINDLE_OVERRIDE = 0.5
    MAX_SPINDLE_OVERRIDE = 1.2
    DEFAULT_LINEAR_VELOCITY = 50.00
    MIN_LINEAR_VELOCITY = 0
    MAX_LINEAR_VELOCITY = 200.00
    DEFAULT_ANGULAR_VELOCITY = 36.00
    MIN_ANGULAR_VELOCITY = 0
    MAX_ANGULAR_VELOCITY = 45.00
    INTRO_GRAPHIC = linuxcnc.gif
    INTRO_TIME = 5
    PROGRAM_PREFIX = ~/linuxcnc/nc_files
    INCREMENTS = 50mm 10mm 5mm 1mm .5mm .1mm .05mm .01mm

    [KINS]
    JOINTS = {project['joints']}
    #KINEMATICS =trivkins coordinates={axis_str} kinstype=BOTH
    KINEMATICS =trivkins coordinates={axis_str}

    [FILTER]
    PROGRAM_EXTENSION = .py Python Script
    py = python

    [TASK]
    TASK = milltask
    CYCLE_TIME = 0.010

    [RS274NGC]
    PARAMETER_FILE = linuxcnc.var

    [EMCMOT]
    EMCMOT = motmod
    COMM_TIMEOUT = 1.0
    COMM_WAIT = 0.010
    BASE_PERIOD = 0
    SERVO_PERIOD = 1000000

    [HAL]
    HALFILE = remora.hal
    POSTGUI_HALFILE = postgui_call_list.hal

    [TRAJ]
    COORDINATES =  {axis_str2}
    LINEAR_UNITS = mm
    ANGULAR_UNITS = degree
    CYCLE_TIME = 0.010
    DEFAULT_LINEAR_VELOCITY = 50.00
    MAX_LINEAR_VELOCITY = 200.00
    NO_FORCE_HOMING = 1 

    [EMCIO]
    EMCIO = io
    CYCLE_TIME = 0.100
    TOOL_TABLE = tool.tbl

    """)


    for num in range(min(project['joints'], len(axis_names))):
        cfgini_data.append(f"""[AXIS_{axis_names[num]}]
    MAX_VELOCITY = 450
    MAX_ACCELERATION = 750.0
    MIN_LIMIT = -1300
    MAX_LIMIT = 1300

    [JOINT_{num}]
    TYPE = LINEAR
    HOME = 0.0
    MIN_LIMIT = -1300
    MAX_LIMIT = 1300
    MAX_VELOCITY = 450.0
    MAX_ACCELERATION = 750.0
    STEPGEN_MAXACCEL = 2000.0
    SCALE = 800.0
    FERROR = 2
    MIN_FERROR = 2.0
    HOME_OFFSET = 0.0
    HOME_SEARCH_VEL = 0
    HOME_LATCH_VEL = 0
    HOME_SEQUENCE = 0

    """)
    open(f"{project['LINUXCNC_PATH']}/ConfigSamples/remora.ini", "w").write("\n".join(cfgini_data))


    cfghal_data = []
    cfghal_data.append(f"""
    # load the realtime components

        loadrt [KINS]KINEMATICS
        loadrt [EMCMOT]EMCMOT base_period_nsec=[EMCMOT]BASE_PERIOD servo_period_nsec=[EMCMOT]SERVO_PERIOD num_joints=[KINS]JOINTS
        loadrt remora

    # estop loopback, SPI comms enable and feedback
        net user-enable-out 	<= iocontrol.0.user-enable-out		=> remora.SPI-enable
        net user-request-enable <= iocontrol.0.user-request-enable	=> remora.SPI-reset
        net remora-status 	<= remora.SPI-status 			=> iocontrol.0.emc-enable-in

    # add the remora and motion functions to threads
        addf remora.read servo-thread
        addf motion-command-handler servo-thread
        addf motion-controller servo-thread
        addf remora.update-freq servo-thread
        addf remora.write servo-thread

    """)

    for num in range(min(project['joints'], len(axis_names))):
        cfghal_data.append(f"""# Joint {num} setup

        setp remora.joint.{num}.scale 		[JOINT_{num}]SCALE
        setp remora.joint.{num}.maxaccel 	[JOINT_{num}]STEPGEN_MAXACCEL

        net {axis_names[num].lower()}pos-cmd 		<= joint.{num}.motor-pos-cmd 	=> remora.joint.{num}.pos-cmd  
        net j{num}pos-fb 		<= remora.joint.{num}.pos-fb 	=> joint.{num}.motor-pos-fb
        net j{num}enable 		<= joint.{num}.amp-enable-out 	=> remora.joint.{num}.enable

    """)

    open(f"{project['LINUXCNC_PATH']}/ConfigSamples/remora.hal", "w").write("\n".join(cfghal_data))

