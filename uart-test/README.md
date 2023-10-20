# gates
UART-TEST

<br>

<ul>

<li><b>Simulation is the only this currently working.</b></li>
<li><b>Implementation is next.</b></li>
</ul>
<br>
<b>To run simulation:</b>
> cd /build/repo/gates/
> source ise-project-sourceme.env
> cd uart-test/xilinx
> ise ./uart-top/uart-top.xise &

**ISE starts**

1) Make sure simulation radio button is selected
2) Click on uart_tb under hierarchy.
3) Expand iSim Simulator in pane below
4) Double click on "Simulate Behavioral Model"

**iSim will start**
5) Click on ISIM> and enter:
> run 200us
6) Click on waveform and hit F6






