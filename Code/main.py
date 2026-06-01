# -------------------------------------------------------------------------
# Ultrasonic Theremin
# Mike Christle Feb 2026
# -------------------------------------------------------------------------

from machine import Pin, SPI
from mcp42010 import MCP42010
from sn76489 import SN76489
from sequencer import Sequencer
from measure import Measure
from machine import reset


LEFT_FREQ_LO = 65.41
LEFT_FREQ_HI = 493.88
RIGHT_FREQ_LO = 130.81
RIGHT_FREQ_HI = 987.77


cntr = 0
# -------------------------------------------------------------------------
def process_left(_):
    global cntr

    ll = mll.get()
    lm = mlm.get()
    if trace_left:
        print(f'process_left {ll} {lm} {cntr}   \r', end='')
        cntr += 1

    if ll or lm < 0:
        return

    left_pitch = lm - ll
    left_volume = lm + ll
    pots.write(MCP42010.POT0, left_volume)


# -------------------------------------------------------------------------
def process_right(_):
    global cntr

    rm = mrm.get()
    rr = mrr.get()
    if trace_right:
        print(f'process_right {rm} {rr} {cntr}   \r', end='')
        cntr += 1

    if rm or rr < 0:
        return

    right_pitch = rr - rm
    right_volume = rr + rm
    pots.write(MCP42010.POT1, right_volume)


# -------------------------------------------------------------------------
# Setup pins
pin_dl0 = Pin(19, mode=Pin.OUT)
pin_dl1 = Pin(20, mode=Pin.OUT)
pin_dr0 = Pin(21, mode=Pin.OUT)
pin_dr1 = Pin(22, mode=Pin.OUT)

pin_rl = Pin(18, mode=Pin.IN)
pin_rm = Pin(17, mode=Pin.IN)
pin_rr = Pin(16, mode=Pin.IN)

# spi, cs_pin, clk_pin, tx_pin
pots = MCP42010(0, 1, 2, 3)

# smn, first_pin
audio = SN76489(7, 4)

# smn, tx_pin, rx_pin
mll = Measure(2, pin_dl0, pin_rl)
mlm = Measure(3, pin_dl0, pin_rm)
mrm = Measure(5, pin_dr0, pin_rm)
mrr = Measure(6, pin_dr0, pin_rr)

# right_cb, left_cb, pins
pins = 19, 18, 17, 16
seq = Sequencer(process_right, process_left, pin_dl0)

trace_left = False
trace_right = True

FACTORS = [
    1.0,          # P1
    1.0 + 1/12,   # m2
    1.0 + 2/12,   # M2
    1.0 + 3/12,   # m3
    1.0 + 4/12,   # M3
    1.0 + 5/12,   # P4
    1.0 + 6/12,   # a4
    1.0 + 7/12,   # P5
    1.0 + 8/12,   # m6
    1.0 + 9/12,   # M6
    1.0 + 10/12,  # m7
    1.0 + 11/12,  # M7
    2.0,          # P8
    2.0,          # 2X
    3.0,          # 3X
    4.0,          # 4X
    5.0,          # 5X
    6.0,          # 6X
    7.0,          # 7X
    8.0,          # 8X
    9.0,          # 9X
    ]


MENU = '''
x       Exit
tl      Enable trace mode for left side.
tr      Enable trace mode for right side.

L2F N   Set left voice 2 to frequency N.
L2A N   Set left voice 2 to attenuation N. 
L3F N   Set left voice 3 to frequency N.
L3A N   Set left voice 2 to attenuation N. 

R2F N   Set right voice 2 to frequency N.
R2A N   Set right voice 2 to attenuation N. 
R3F N   Set right voice 3 to frequency N.
R3A N   Set right voice 3 to attenuation N. 
'''

while True:
    cmd = input('= ').split()
    cnt = len(cmd)

    if cnt == 0:
        print(MENU)
        continue
    if cmd[0] == 'x':
        break
    if cmd[0] == 'tl':
        trace_left = True
        input('Press return to stop\n')
        trace_left = False
        print()
    if cmd[0] == 'tr':
        trace_right = True
        input('Press return to stop\n')
        trace_right = False
        print()
    if cnt == 1:
        continue

    val = int(cmd[1])
    if cmd[0] == 'L2F':
        audio.set_factor(0, 2, FACTORS[val])
    if cmd[0] == 'L3F':
        audio.set_factor(0, 3, FACTORS[val])
    if cmd[0] == 'R2F':
        audio.set_factor(1, 2, FACTORS[val])
    if cmd[0] == 'R3F':
        audio.set_factor(1, 3, FACTORS[val])

    if cmd[0] == 'L2V':
        audio.set_atten(0, 2, val)
    if cmd[0] == 'L3V':
        audio.set_atten(0, 3, val)
    if cmd[0] == 'R2V':
        audio.set_atten(1, 2, val)
    if cmd[0] == 'R3V':
        audio.set_atten(1, 3, val)

reset()

