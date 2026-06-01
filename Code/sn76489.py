# -------------------------------------------------------------------------
# SN76489 Sound Generator PIO Code
# Mike Christle 2026
#
# Pin order:
# D0, D1, D2, D3, D4, D5, D6, D7, WER, WEL, READY, CLK
# -------------------------------------------------------------------------
from machine import Pin, PWM
import rp2


CLK_FREQ = 654_720


class SN76489:
    def __init__(self, smn, pin):
        '''
        Driver for the SN76489 audio generator chips.
        smn    State machine number.
        pin    GPIO number of the first pin.
        '''
        self.d7 = Pin(pin,     Pin.OUT)
        self.d6 = Pin(pin + 1, Pin.OUT)
        self.d5 = Pin(pin + 2, Pin.OUT)
        self.d4 = Pin(pin + 3, Pin.OUT)
        self.d3 = Pin(pin + 4, Pin.OUT)
        self.d2 = Pin(pin + 5, Pin.OUT)
        self.d1 = Pin(pin + 6, Pin.OUT)
        self.d0 = Pin(pin + 7, Pin.OUT)

        self.wel = Pin(pin +  8, Pin.OUT, value=1) # WEn & CEn
        self.wer = Pin(pin +  9, Pin.OUT, value=1) # WEn & CEn
        self.rdy = Pin(pin + 10, Pin.IN)

        self.clk = Pin(pin + 11, Pin.OUT)
        self.clk_pwm = PWM(self.clk,
                           freq=CLK_FREQ,
                           duty_u16=32_768)
#         freq = self.clk_pwm.freq()
#         print(freq)

        self.sm = rp2.StateMachine(
            smn,
            self.sm_code,
            freq=10_000_000,
            out_base=self.d7,
            set_base=self.wel,
            jmp_pin=self.rdy,
            )
        self.sm.active(1)

        # Turn off all outputs
        self.write_reg(0, 1, 0x0F)
        self.write_reg(0, 3, 0x0F)
        self.write_reg(0, 5, 0x0F)
        self.write_reg(0, 7, 0x0F)
        self.write_reg(1, 1, 0x0F)
        self.write_reg(1, 3, 0x0F)
        self.write_reg(1, 5, 0x0F)
        self.write_reg(1, 7, 0x0F)

        self.factors = [[0.0, 0.0], [0.0, 0.0]]
        self.attens = [[15, 15], [15, 15]]

    # ---------------------------------------------------------------------
    def set_factor(self, chip, chan, data):
        '''
        Set the frequency factor for a voice.
        chip    Chip number, 0 or 1.
        chan    Channel number, 2 or 3.
        data    Factor value.
        '''

        if chip < 0 or chip > 1:
            raise ValueError('Chip out of range, 0, 1.')

        if chan < 2 or chan > 3:
            raise ValueError('Channel number out of range, 2 or 3.')

        
        self.factors[chip][chan - 2] = data

    # ---------------------------------------------------------------------
    def set_atten(self, chip, chan, data):
        '''
        Set the attenuation for a voice.
        chip    Chip number, 0 or 1.
        chan    Channel number, 2 or 3.
        data    Attenuation value.
        '''

        if chip < 0 or chip > 1:
            raise ValueError('Chip out of range, 0, 1.')

        if chan < 2 or chan > 3:
            raise ValueError('Channel number out of range, 2 or 3.')

        
        self.attens[chip][chan - 2] = data

    # ---------------------------------------------------------------------
    def write_reg(self, chip, adrs, data):
        '''
        Write value to a register.
        chip    Chip number, 0 or 1.
        adrs    Address to write, 0 to 7.
        data    Data value.
        '''

        value = (chip << 8) | 0x80 | (adrs << 4) | (data & 0x0F)
        # print(f'value 1 {value:08X}')
        self.sm.put(value)
        if adrs == 0 or adrs == 2 or adrs == 4:
            value = (chip << 8) | (data >> 4)
            # print(f'value 2 {value:08X}')
            self.sm.put(value)

    # ---------------------------------------------------------------------
    def write_freq(self, chip, chan, freq):
        '''
        chip   Chip to write.     0, 1
        chan   Channel to write.  0, 1, 2
        freq   Frequency.         20 to 20K Hz
               
        '''

        if chip < 0 or chip > 1:
            raise ValueError('Chip out of range, 0, 1.')

        if chan < 0 or chan > 2:
            raise ValueError('Channel out of range, 0, 1, 2.')

        if freq < 20 or freq > 20_000:
            raise ValueError('Frequency out of range, 20 to 20K Hz.')

        freq = int(CLK_FREQ / 32 / freq)
        adrs = chan * 2
        self.write_reg(chip, adrs, freq)

    # ---------------------------------------------------------------------
    def write_attn(self, chip, chan, attn):
        '''
        chip   Chip to write.     0, 1
        chan   Channel to write.  0, 1, 2
        attn   Attenuation.       0 to 30 db in 2db increments
               
        '''

        if chip < 0 or chip > 1:
            raise ValueError('Chip out of range, 0, 1.')

        if chan < 0 or chan > 2:
            raise ValueError('Channel out of range, 0, 1, 2.')

        if attn < 0 or attn > 30:
            raise ValueError('Attenuation out of range, 0 to 30 db.')

        attn //= 2
        adrs = chan * 2
        self.write_reg(chip, adrs + 1, attn)

    # ---------------------------------------------------------------------
    def update(chip, freq):
        '''
        Update the frequency and attenuation for a channel.
        chip    Chip number, 0 or 1.
        freq    Frequency for voice 1.
        '''

        write_freq(chip, 0, freq)
        write_freq(chip, 1, freq * self.factor[chip][0])
        write_freq(chip, 2, freq * self.factor[chip][1])

        write_attn(chip, 1, self.factor[chip][0])
        write_attn(chip, 2, self.factor[chip][1])

    # ---------------------------------------------------------------------
    @rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_RIGHT,
                 fifo_join=rp2.PIO.JOIN_TX,
                 set_init=(rp2.PIO.OUT_HIGH, rp2.PIO.OUT_HIGH),
                 out_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW,
                           rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW,
                           rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW,
                           rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW))
    def sm_code():

        label('lbl0')
        set(pins, 3)        # Clear WE
        pull(block)         # Wait for nect command
        out(pins, 8)        # Output data byte
        out(y, 24)          # Which channel?
        jmp(not_y, 'lbl1')

        set(pins, 1)        # Assert WERn
        jmp('lbl2')

        label('lbl1')
        set(pins, 2) [1]    # Assert WELn

        label('lbl2')
        jmp(pin, 'lbl0')    # Wait for READY to go high
        jmp('lbl2')


# -------------------------------------------------------------------------
C0  = 7645  # 16.35 Hz
C0S = 7217  # 17.32 Hz
D0  = 6812  # 18.35 Hz
D0S = 6427  # 19.45 Hz
E0  = 6068  # 20.6 Hz
F0  = 5726  # 21.83 Hz
F0S = 5407  # 23.12 Hz
G0  = 5102  # 24.5 Hz
G0S = 4815  # 25.96 Hz
A0  = 4545  # 27.5 Hz
A0S = 4290  # 29.14 Hz
B0  = 4049  # 30.87 Hz
C1  = 3823  # 32.7 Hz
C1S = 3608  # 34.65 Hz
D1  = 3405  # 36.71 Hz
D1S = 3214  # 38.89 Hz
E1  = 3034  # 41.2 Hz
F1  = 2864  # 43.65 Hz
F1S = 2703  # 46.25 Hz
G1  = 2551  # 49.0 Hz
G1S = 2408  # 51.91 Hz
A1  = 2273  # 55.0 Hz
A1S = 2145  # 58.27 Hz
B1  = 2025  # 61.74 Hz
C2  = 1911  # 65.41 Hz
C2S = 1804  # 69.3 Hz
D2  = 1703  # 73.42 Hz
D2S = 1607  # 77.78 Hz
E2  = 1517  # 82.41 Hz
F2  = 1432  # 87.31 Hz
F2S = 1351  # 92.5 Hz
G2  = 1276  # 98.0 Hz
G2S = 1204  # 103.83 Hz
A2  = 1136  # 110.0 Hz
A2S = 1073  # 116.54 Hz
B2  = 1012  # 123.47 Hz
C3  =  956  # 130.81 Hz
C3S =  902  # 138.59 Hz
D3  =  851  # 146.83 Hz
D3S =  804  # 155.56 Hz
E3  =  758  # 164.81 Hz
F3  =  716  # 174.61 Hz
F3S =  676  # 185.0 Hz
G3  =  638  # 196.0 Hz
G3S =  602  # 207.65 Hz
A3  =  568  # 220.0 Hz
A3S =  536  # 233.08 Hz
B3  =  506  # 246.94 Hz
C4  =  478  # 261.63 Hz
C4S =  451  # 277.18 Hz
D4  =  426  # 293.66 Hz
D4S =  402  # 311.13 Hz
E4  =  379  # 329.63 Hz
F4  =  358  # 349.23 Hz
F4S =  338  # 369.99 Hz
G4  =  319  # 392.0 Hz
G4S =  301  # 415.3 Hz
A4  =  284  # 440.0 Hz
A4S =  268  # 466.16 Hz
B4  =  253  # 493.88 Hz
C5  =  239  # 523.25 Hz
C5S =  225  # 554.37 Hz
D5  =  213  # 587.33 Hz
D5S =  201  # 622.25 Hz
E5  =  190  # 659.26 Hz
F5  =  179  # 698.46 Hz
F5S =  169  # 739.99 Hz
G5  =  159  # 783.99 Hz
G5S =  150  # 830.61 Hz
A5  =  142  # 880.0 Hz
A5S =  134  # 932.33 Hz
B5  =  127  # 987.77 Hz
C6  =  119  # 1046.5 Hz
C6S =  113  # 1108.73 Hz
D6  =  106  # 1174.66 Hz
D6S =  100  # 1244.51 Hz
E6  =   95  # 1318.51 Hz
F6  =   89  # 1396.91 Hz
F6S =   84  # 1479.98 Hz
G6  =   80  # 1567.98 Hz
G6S =   75  # 1661.22 Hz
A6  =   71  # 1760.0 Hz
A6S =   67  # 1864.66 Hz
B6  =   63  # 1975.53 Hz
C7  =   60  # 2093.0 Hz
C7S =   56  # 2217.46 Hz
D7  =   53  # 2349.32 Hz
D7S =   50  # 2489.02 Hz
E7  =   47  # 2637.02 Hz
F7  =   45  # 2793.83 Hz
F7S =   42  # 2959.96 Hz
G7  =   40  # 3135.96 Hz
G7S =   38  # 3322.44 Hz
A7  =   36  # 3520.0 Hz
A7S =   34  # 3729.31 Hz
B7  =   32  # 3951.07 Hz
C8  =   30  # 4186.01 Hz
C8S =   28  # 4434.92 Hz
D8  =   27  # 4698.64 Hz
D8S =   25  # 4978.03 Hz

# -------------------------------------------------------------------------
if __name__ == "__main__":

    from time import sleep

    MENU = (
    'x         Exit\n'
    'f n c v   Set chip n channel c to frequency v\n'
    'a n c v   Set chip n channel c to attenuation v\n'
    )

    sn = SN76489(0, 0)
    print(MENU)
    while True:
        cmd = input('> ').split()
        cnt = len(cmd)
        if cnt < 1:
            print(MENU)
        elif cmd[0] == 'x':
            break
        elif cnt != 4:
            continue
        elif cmd[0] == 'f':
            chip = int(cmd[1])
            chan = int(cmd[2])
            freq = int(cmd[3])
            sn.write_freq(chip, chan, freq)
        elif cmd[0] == 'a':
            chip = int(cmd[1])
            chan = int(cmd[2])
            attn = int(cmd[3])
            sn.write_attn(chip, chan, attn)
