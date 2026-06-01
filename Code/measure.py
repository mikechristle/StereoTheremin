# -------------------------------------------------------------------------
# Audio Theremin, Travel Time Measure PIO COde
# Mike Christle 2026
# -------------------------------------------------------------------------

import rp2


class Measure:
    def __init__(self, smn, tx_pin, rx_pin):
        '''
        Initialize a measure travel time state machine.
        smn     State Machine Number
        tx_pin  Pin to monitor for start time
        rx_pin  Pin to mark end time
        '''

        self.sm = rp2.StateMachine(
            smn,
            self.measure,
            freq=200_000,
            in_base=tx_pin,
            jmp_pin=rx_pin,
            )

        self.MAX_VAL = 300
        self.sm.active(1)
        self.sm.put(self.MAX_VAL)

    # ----------------------------------------------------------------------
    def get(self):
        '''
        Get a value from the state machine.
        Returns zero if no value in the fifo.
        '''

        val = -1
        while self.sm.rx_fifo() > 0:
            val = self.MAX_VAL - self.sm.get()
            if val < 0:
                val = 0
        return val

    # ----------------------------------------------------------------------
    # PIO Program to measure delay from transmit to receive
    # ----------------------------------------------------------------------
    @rp2.asm_pio() 
    def measure():
        pull(block)

        wrap_target()
        mov(x, osr)
        wait(1, pin, 0)

        label('lbl1')
        jmp(x_dec, 'lbl2')
        jmp('lbl3')
        
        label('lbl2')
        jmp(pin, 'lbl1')

        label('lbl3')
        mov(isr, x)
        push(noblock)
        wrap()


if __name__ == "__main__":

    from machine import Pin
    from time import sleep, sleep_us

    tx_pin = Pin(15, Pin.OUT, value=0)
    rx_pin = Pin(14, Pin.IN)
    tst_pin = Pin(13, Pin.OUT, value=1)

    meas = Measure(0, tx_pin, rx_pin)

    delays = [500, 1000, 1500, 2000, 2500, 3000]
    for delay in delays:
        tx_pin.high()
        sleep_us(2)
        tx_pin.low()
        sleep_us(delay)
        tst_pin.low()
        sleep_us(2)
        tst_pin.high()
        sleep(1.0)
        val = meas.get()
        print(f'{delay:6} {val}')
        
