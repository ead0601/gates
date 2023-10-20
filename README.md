# gates
Multiple FPGA/CPLD designs

<br>

<ul>

<li><b>Please start with the gates/doc/how-to-build-enivronment.md document.</b></li>
<li><b>Then look at the gates/led-blink project. Use this as a pipe-flush to sort out your ISE install and JTAG burn process.</b></li>
<li><b>All of the other stuff in the gates folder is currently WIP.</b></li>
<li><b>Next module to be completed is a UART hello-world. So that we can have output for debug.</b></li>
<li><b>After that is a 4KHz SDIO card read to UART dump, via button push for sector advance. Where sector data will be analyzed vs the raw image file that was written to the uSD card, bad block detection will be investiagted.</b></li>
<li><b>Then comes a 4 bit SDIO block burst write test with raw image analysis.</b></li>
<li><b>Finally the 40 pin data capture can be dumped as an SDIO block burst to the uSD card.</b></li>

</ul>

