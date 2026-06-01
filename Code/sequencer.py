# -------------------------------------------------------------------------
# Stereo Theremin, Sequencer PIO Code
# Mike Christle 2025
# -------------------------------------------------------------------------
# To sense the location of the players hands I use ultrasonic transmitters
# and receivers. The following diagram shows the arrangement.
#
#        L       R
#
#    X   A   Y   B   Z
#
# There are two ultrasonic transmitters, A and B, three ultrasonic
# receivers, X, Y and Z, and two players hands, L and R. First transmitter
# A transmits a series of pulses which reflect off hand L and is received
# by receivers X and Y. The controller measures the time of flight for
# ALX and ALY. Next transmitter B transmits a series of pulses which
# reflect off hand R and is received by receivers Y and Z. The controller
# measures the time of flight for BRY and BRZ.
#
# This class creates six state machines, two to output the pulses on A
# and B, and controls the overall system timing. The remaining four
# measure the time of flight for ALX, ALY, BRY, and BRZ. Then these
# values are passed to two callback functions to process.
#
# This class hardcodes the state machine numbers, using 2 thru 7.
# This leaves 0 and 1 free.
#
# The pin numbers are given in a tuple in the following order:
# (DL, DR, RL, RM, RR)
# For DL and DR pairs must be contigious. Gif the lowest GPIO number.
# -------------------------------------------------------------------------
from machine import Pin, Timer
from array import array
from time import sleep, ticks_ms, ticks_us, ticks_diff

import rp2


class Sequencer:
    def __init__(self, right_cb, left_cb, pin):
        '''
        Drives the timing sequence for transmit signals.
        right_cb   Callback function for right side.
        left_cb    Callback function for left side.
        pin        First pin.
        '''

        # Sets 50 mSec cycle delay count
        CYCLE_DELAY_COUNT = 250

        # Left State Machine
        self.sm_dl = rp2.StateMachine(
            0,
            self.drive_left_sm,
            freq=160_000,
            set_base=pin,
            )
        self.sm_dl.irq(left_cb)
        self.sm_dl.put(CYCLE_DELAY_COUNT)

        # Right State Machine
        self.sm_dr = rp2.StateMachine(
            1,
            self.drive_right_sm,
            freq=160_000,
            )
        self.sm_dr.irq(right_cb)

        # Start the state machines running
        self.sm_dr.active(1)
        self.sm_dl.active(1)

    # ----------------------------------------------------------------------
    def stop(self):
        self.sm_dl.active(0)
        self.sm_dr.active(0)
        self.sm_dl.restart()
        self.sm_dr.restart()

    # ----------------------------------------------------------------------
    # PIO Programs to output 40KHz pulses and interrupts
    # ----------------------------------------------------------------------
    @rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW,
                           rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW)) 
    def drive_left_sm():

        pull(block)
        wrap_target()

        # Output 10 pulses
        set(x, 10)
        label('lbl1')
        set(pins, 0b0001) [1]
        set(pins, 0b0010)
        jmp(x_dec, 'lbl1')
        set(pins, 0)

        # Delay 50 mSec, 8000 clocks
        mov(x, osr)
        label('lbl2')
        nop() [30]
        jmp(x_dec, 'lbl2')

        # Set interrupt to trigger left side processing
        irq(rel(0))

        # Output 10 pulses
        set(x, 10)
        label('lbl3')
        set(pins, 0b0100) [1]
        set(pins, 0b1000)
        jmp(x_dec, 'lbl3')
        set(pins, 0)

        # Delay 50 mSec, 8000 clocks
        mov(x, osr)
        label('lbl4')
        nop() [30]
        jmp(x_dec, 'lbl4')

        # Set interrupt to trigger right side pulses
        irq(7)
        wrap()

    # ----------------------------------------------------------------------
    # PIO Programs to output 40KHz pulses and interrupts
    # ----------------------------------------------------------------------
    @rp2.asm_pio() 
    def drive_right_sm():

        # Wait for left to output pulses
        wait(1, irq, 7)

        # Set interrupt to trigger right side processing
        irq(rel(0))
