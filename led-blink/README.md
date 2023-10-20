**README.md**

In this project we will be designing a simple digital circuit that blinks a series of LEDs. Normally the verilog RTL would exist in a top directory parallel to the xilinx folder. The normal flow is to keep a series of top-level design modules(folders) that are then synthesized into single design. Each top-level folder contains all of the RTL needed for that one module.

This was not done for this design, since this design was meant as a single encapsulated pipe-flush example.

All of the data in folders parallel to xilinx are meant to be non-volatile design implmentations. The project's compile process is performed within the projects respective xilinx folder. Therefore, keeping any volatile and non-volatile data seperated.
