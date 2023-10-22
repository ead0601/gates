# RAW DATA FORMAT<br>
We will break a 40 pin header into 2 sets of 20pin sections, where each 20 pin section will be stored in a 32 bit container.

**[32 BIT CONTAINER]**<br>
D31  T9 : (100Mhz timer)  INTERNAL TIMER COUNT<br>
D30  T8 : " <br>
D29  T7 : " <br>
D28  T6 : " <br>
D27  T5 : " <br>
D26  T4 : " <br>
D25  T3 : " <br>
D24  T2 : " <br>
D23  T1 : " <br>
D22  T0 : (100Mhz timer)  INTERNAL TIMER COUNT<br>
<br>
D21  DATA : D21......PWR/GND (digital sample for slump/bump detection)<br>
D20  DATA : D20......(32KHz timer)   EXTERNAL TIMER PULSE<br>
<br>
D19  DATA : D19......IC DATA<br>
D18  DATA : D18......IC DATA<br>
D17  DATA : D17......IC DATA<br>
. . .<br>
D00  DATA : D0.......IC DATA<br>


The 32bit container will only be pushed to storage if any of the DATA pins toggle. The internal timer is used to encode timing reference for sampled signal, upon roll-over event a sample storage will be forced even if no DATA pin was toggled. External timer pulse input event is used to sync multiple DIP samplers when combing raw data streams.<br>

It is preferred that high frequency signals are collocated on a 32-bit container, in order to minimize stored data to SDIO card. The two 20 pin sets will be stored in two 32 bit container packets (total 64 bits), only when respective data within the container changes.<br>

-----------------------------------------------------------------------------------

# SPI FORMAT FOR (4 BIT SPI, CE0, CE1, CLK, D3-D0)<br>
CE1  : CHIP ENABLE 1 USED FOR COMMAND SEQUENCE<br>
CE0  : CHIP ENABLE 0 USED FOR READ DATA<br>

**COMMAND**<br>
C07  : ENABLEDEV : DEVICEID[2]<br>
C06  : ENABLEDEV : DEVICEID[1]<br>
C05  : ENABLEDEV : DEVICEID[0]<br>
C06  : SETSECT	 : SET SECTOR NUMBER<br>
C03  : SETTRIG	 : SET TRIG PIN<br>
C04  : STOPACQ	 : STOP ACQ<br>
C01  : STARTACQ	 : START ACQ<br>
C00  : RESERVED<br>
(followed by)<br>
T00  : TRIG PIN ( 8bits) : (0-40) pins<br>
(or)<br>
S00  : SECTOR NUMBER (64 bits) : UPDATE CURRENT START SECTOR<br>

**DATA**<br>
D7   : MSB  : BYTE 0<br>
. . .<br>
D0   : LSB  : BYTE 0<br>
D7   : MSB  : BYTE 1<br>
. . .<br>



