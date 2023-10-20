**README.md**

Prefered board to use:

piswords: Xilinx spartan6 XC6SLX16 development Core Board Xilinx spartan 6 FPGA 256

<http://piswords.com/xc6slx16.html>

Prefered JTAG programmer:  <b MODEL DLC10 >

Waveshare XILINX JTAG Download Debugger Compatible XILINX Platform Cable USB FPGA CPLD in-Circuit Debugger Programmer

<http: https://www.amazon.com/Compatible-Platform-Cable-USB-Programmer/dp/B00KM70UFG/ref=sr_1_1?crid=3ERK3RS84AWPR&keywords=Waveshare+XILINX+JTAG+Download+Debugger+Compatible+XILINX+Platform+Cable+USB+FPGA+CPLD+in-Circuit+Debugger+Programmer&qid=1697765070&s=electronics&sprefix=waveshare+xilinx+jtag+download+debugger+compatible+xilinx+platform+cable+usb+fpga+cpld+in-circuit+debugger+programmer%2Celectronics%2C131&sr=1-1>



1)  **Install GIT repo (in a specific location)**

> mkdir /build/repo
>
> cd /build/repo
>
> git clone https://github.com/ead0601/gates

2)  **Download ISE 14.7 **

The Xilinx tool needed for this project is:

<https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/archive-ise.html>

Select 14.7 and **Full Installer for Linux (TAR/GZIP - 6.09 GB), for
download**

3)  **Un-compress and execute:**

> mkdir /build/tools/Xilinx
>
> (un-tar into a temp location, NOT the directory above)
> tar -xvf Xilinx\_ISE\_DS\_Lin\_14.7\_1015\_1.tar  
>
> cd Xilinx\_ISE\_DS\_Lin\_14.7\_1015\_1
>
>./xsetup (run)

When prompted selected the install Xilinx ISE path into:

**/build/tools/Xilinx**

When prompted for Edition List select:

**ISE Design Suite Systems Edition**

4)  **Create a Xilinx account and download a free license:**

    [**https://www.xilinx.com/support/licensing\_solution\_center.html**](https://www.xilinx.com/support/licensing_solution_center.html)

    Select "Obtain a license for Legacy IP Core Products", Xilinx
    Product Licensing Site

    Select ISE Embedded Edition License, Certificate -- No Charge, and a
    license file will be e-mailed to you.

5)  **Source env scripts:**

    source /build/tools/Xilinx/14.7/ISE\_DS/settings64.sh (bash)

> ise & (to execute ISE)

6)  **Setup license:**

    The first time you execute "ise", a license select tool will be
    launched. At this point select the file of the keyfile you received
    from step 4:

-------------------------------------------------------------------------
**Good Video for License Setup**

https://www.youtube.com/watch?v=yzEIQLQZYpk&t=2s

-------------------------------------------------------------------------

PER-PROJECT:

7)  **Starting ISE:**

>    cd /build/repo/gates/{desired-project}/Xilinx

    **All project related enviroment settings added to this file**
>    
>    source /build/repo/gates/{desired-project}/sourceme-project.env 

    **Start ISE**
>    
>  cd xilinx
>    
>  ise &

    Open project {desire-project}-top.xise


8) TO BURN:

>  sudo apt -y install xc3sprog

   Go to directory of .bit file  (in a window where you did not source ISE env)

> xc3sprog -c xpc -v -p 0 ./{FILENAME}.bit



