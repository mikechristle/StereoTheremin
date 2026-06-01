# -------------------------------------------------------------------------
# MCP42010 Digital Potentiometer SPI Driver
# Mike Christle Feb 2026
# -------------------------------------------------------------------------

from machine import Pin, SPI


class MCP42010:
    POT0 = 0x11
    POT1 = 0x12

    def __init__(self, spi, cs, clk, tx):
        '''
        Constructor for MCP42010 driver
        spi  The SPI channel 0, 1
        cs   The chip select signal GPIO number
        clk  The SCLK signal GPIO number
        tx   The MOSI signal GPIO number
        '''

        self.data = bytearray(2)
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.spi = SPI(spi,
                       sck=Pin(clk),
                       mosi=Pin(tx),
                       )

    def write(self, pot, value):
        '''
        Write a value to a potentiometer
        pot    Pot number      POT0, POT1
        value  Value to write  0-255
        '''

        self.data[0] = pot
        self.data[1] = value
        self.cs(0)
        self.spi.write(self.data)
        self.cs(1)


# -------------------------------------------------------------------------
if __name__ == "__main__":
    from time import sleep

    mcp = MCP42010(1, 13, 14, 15)
    for x in range(0, 256, 4):
        mcp.write(MCP42010.POT0, x)
        mcp.write(MCP42010.POT1, 255 - x)
        print(x)
        sleep(1.0)

    print('Pot Value')
    pots = MCP42010.POT0, MCP42010.POT1
    while True:
        cmd = input('> ').split()
        if len(cmd) == 2:
            pot = pots[int(cmd[0])]
            value = int(cmd[1])
            mcp.write(pot, value)
