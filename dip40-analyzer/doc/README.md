# RAW DATA FORMAT

We will break a 40 pin header into 2 sets of 20pin sections, where each 20 pin section will be stored in a 32 bit container.

**[32 BIT CONTAINER]**
D31  T9             (100Mhz timer)  INTERNAL TIMER COUNT
D30  T8              .
D29  T7              .
D28  T6              .
D27  T5              .
D26  T4              .
D25  T3              .
D24  T2              .
D23  T1              .
D22  T0             (100Mhz timer)  INTERNAL TIMER COUNT
D21  DATA – D21     PWR/GND (digital sample for slump/bump detection)
D20  DATA – D20     (32KHz timer)   EXTERNAL TIMER PULSE
D19  DATA - D19     IC DATA
…
D00  DATA - D0      IC DATA


The 32bit container will only be pushed to storage if any of the DATA pins toggle. The internal timer is used to encode timing reference for sampled signal, upon roll-over event a sample storage will be forced even if no DATA pin was toggled. External timer pulse input event is used to sync multiple DIP samplers when combing raw data streams.

It is preferred that high frequency signals are collocated on a 32-bit container, in order to minimize stored data to SDIO card. The two 20 pin sets will be stored in two 32 bit container packets (total 64 bits), only when respective data within the container changes.

-----------------------------------------------------------------------------------

# SPI FORMAT FOR (4 BIT SPI, CE0, CE1, CLK, D3-D0)

CE0  : CHIP ENABLE 0 USED FOR READ DATA
CE1  : CHIP ENABLE 1 USED FOR COMMAND SEQUENCE

**COMMAND**
C07  : COMMAND : 8 BITS
            SETSECT      : SET SECTOR NUMBER
            SETTRIG      :
            STOPTRIG     :
C00         STARTTRIG    :

T00  : TRIG PIN : (0-40) pins

S00  : SECTOR NUMBER : 64 bits


**DATA**
D7   : MSB  : BYTE 0
. . .
D0   : LSB  : BYTE 0
D7   : MSB  : BYTE 1
. . .



