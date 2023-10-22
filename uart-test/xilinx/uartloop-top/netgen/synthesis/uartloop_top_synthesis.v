////////////////////////////////////////////////////////////////////////////////
// Copyright (c) 1995-2013 Xilinx, Inc.  All rights reserved.
////////////////////////////////////////////////////////////////////////////////
//   ____  ____
//  /   /\/   /
// /___/  \  /    Vendor: Xilinx
// \   \   \/     Version: P.20131013
//  \   \         Application: netgen
//  /   /         Filename: uartloop_top_synthesis.v
// /___/   /\     Timestamp: Sat Oct 21 23:09:09 2023
// \   \  /  \ 
//  \___\/\___\
//             
// Command	: -intstyle ise -insert_glbl true -w -dir netgen/synthesis -ofmt verilog -sim uartloop_top.ngc uartloop_top_synthesis.v 
// Device	: xc6slx16-3-ftg256
// Input file	: uartloop_top.ngc
// Output file	: /build/repo/gates/uart-test/xilinx/uartloop-top/netgen/synthesis/uartloop_top_synthesis.v
// # of Modules	: 1
// Design Name	: uartloop_top
// Xilinx        : /build/tools/Xilinx/14.7/ISE_DS/ISE/
//             
// Purpose:    
//     This verilog netlist is a verification model and uses simulation 
//     primitives which may not represent the true implementation of the 
//     device, however the netlist is functionally correct and should not 
//     be modified. This file cannot be synthesized and should only be used 
//     with supported simulation tools.
//             
// Reference:  
//     Command Line Tools User Guide, Chapter 23 and Synthesis and Simulation Design Guide, Chapter 6
//             
////////////////////////////////////////////////////////////////////////////////

`timescale 1 ns/1 ps

module uartloop_top (
  clk, rx_serial, tx_serial
);
  input clk;
  input rx_serial;
  output tx_serial;
  wire clk_BUFGP_0;
  wire rx_serial_IBUF_1;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_2 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_3 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_4 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_5 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_6 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_7 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_8 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_9 ;
  wire \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ;
  wire \UART_TOP_INST/UART_TX_INST/o_Tx_Serial_11 ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ;
  wire \UART_TOP_INST/UART_TX_INST/Mmux__n009541 ;
  wire \UART_TOP_INST/UART_TX_INST/Mmux__n009511 ;
  wire \UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_3_15 ;
  wire \UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_4_16 ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1-In ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2-In ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In_29 ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ;
  wire \UART_TOP_INST/UART_TX_INST/_n0135_inv ;
  wire \UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ;
  wire \UART_TOP_INST/UART_TX_INST/_n0088 ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ;
  wire \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1_46 ;
  wire \UART_TOP_INST/UART_RX_INST/_n0160_inv1 ;
  wire \UART_TOP_INST/UART_RX_INST/_n0153_inv1 ;
  wire \UART_TOP_INST/UART_RX_INST/Mmux__n013511 ;
  wire \UART_TOP_INST/UART_RX_INST/Madd_r_Clock_Count[7]_GND_3_o_add_23_OUT_cy<5> ;
  wire \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1-In ;
  wire \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2-In ;
  wire \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3-In_72 ;
  wire \UART_TOP_INST/UART_RX_INST/_n0146_inv ;
  wire \UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o ;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o ;
  wire \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ;
  wire \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ;
  wire N4;
  wire N6;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ;
  wire N8;
  wire N10;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_dpot_94 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_dpot_95 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_dpot_96 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_dpot_97 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_dpot_98 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_dpot_99 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_dpot_100 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_dpot_101 ;
  wire N12;
  wire \UART_TOP_INST/UART_RX_INST/_n0219_inv1_cepot ;
  wire \UART_TOP_INST/UART_RX_INST/r_Bit_Index_0_dpot_104 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Bit_Index_1_dpot_105 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Bit_Index_2_dpot_106 ;
  wire N14;
  wire N18;
  wire N20;
  wire N22;
  wire N23;
  wire N25;
  wire N28;
  wire N29;
  wire N31;
  wire N32;
  wire N34;
  wire N35;
  wire N40;
  wire N42;
  wire \UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 ;
  wire \UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot ;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count_0_dpot_123 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count_1_dpot_124 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count_2_dpot_125 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count_3_dpot_126 ;
  wire \UART_TOP_INST/UART_RX_INST/r_Clock_Count_4_dpot_127 ;
  wire N44;
  wire N45;
  wire \UART_TOP_INST/UART_RX_INST/Mshreg_r_Rx_Data_130 ;
  wire \NLW_UART_TOP_INST/UART_RX_INST/Mshreg_r_Rx_Data_Q15_UNCONNECTED ;
  wire [2 : 0] \UART_TOP_INST/UART_TX_INST/r_Bit_Index ;
  wire [6 : 0] \UART_TOP_INST/UART_TX_INST/r_Clock_Count ;
  wire [3 : 1] \UART_TOP_INST/UART_TX_INST/_n0121 ;
  wire [8 : 2] \UART_TOP_INST/UART_TX_INST/_n0095 ;
  wire [7 : 0] \UART_TOP_INST/UART_TX_INST/r_Tx_Data ;
  wire [2 : 0] \UART_TOP_INST/UART_RX_INST/r_Bit_Index ;
  wire [7 : 0] \UART_TOP_INST/UART_RX_INST/r_Clock_Count ;
  wire [7 : 1] \UART_TOP_INST/UART_RX_INST/_n0135 ;
  LUT6 #(
    .INIT ( 64'hFD75B931EC64A820 ))
  \UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_3  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [1]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [6]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [7]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [5]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [4]),
    .O(\UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_3_15 )
  );
  LUT6 #(
    .INIT ( 64'hFD75B931EC64A820 ))
  \UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_4  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [1]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [2]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [3]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [1]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [0]),
    .O(\UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_4_16 )
  );
  FD #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2  (
    .C(clk_BUFGP_0),
    .D(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2-In ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 )
  );
  FD #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3  (
    .C(clk_BUFGP_0),
    .D(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In_29 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 )
  );
  FD #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1  (
    .C(clk_BUFGP_0),
    .D(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1-In ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1_46 )
  );
  FDE   \UART_TOP_INST/UART_TX_INST/o_Tx_Serial  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0088 ),
    .Q(\UART_TOP_INST/UART_TX_INST/o_Tx_Serial_11 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_6  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [2]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [6])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_5  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [3]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [5])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_4  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [4]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_3  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [5]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_2  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [6]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_1  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [7]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count_0  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0095 [8]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Bit_Index_2  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/_n0135_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0121 [1]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [2])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Bit_Index_1  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/_n0135_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0121 [2]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [1])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Bit_Index_0  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/_n0135_inv ),
    .D(\UART_TOP_INST/UART_TX_INST/_n0121 [3]),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_7  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_2 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [7])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_6  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_3 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [6])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_5  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_4 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [5])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_4  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_5 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [4])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_3  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_6 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [3])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_2  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_7 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [2])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_1  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_8 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [1])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_TX_INST/r_Tx_Data_0  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_9 ),
    .Q(\UART_TOP_INST/UART_TX_INST/r_Tx_Data [0])
  );
  FD #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2  (
    .C(clk_BUFGP_0),
    .D(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2-In ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 )
  );
  FD #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3  (
    .C(clk_BUFGP_0),
    .D(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3-In_72 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 )
  );
  FD #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1  (
    .C(clk_BUFGP_0),
    .D(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1-In ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_7  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv ),
    .D(\UART_TOP_INST/UART_RX_INST/_n0135 [1]),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_6  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv ),
    .D(\UART_TOP_INST/UART_RX_INST/_n0135 [2]),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [6])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_5  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv ),
    .D(\UART_TOP_INST/UART_RX_INST/_n0135 [3]),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_4  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_4_dpot_127 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_3  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_3_dpot_126 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_2  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_2_dpot_125 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_1  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_1_dpot_124 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_0  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_0_dpot_123 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Bit_Index_2  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0219_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Bit_Index_2_dpot_106 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Bit_Index_1  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0219_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Bit_Index_1_dpot_105 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Bit_Index_0  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0219_inv1_cepot ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Bit_Index_0_dpot_104 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0])
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0160_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_dpot_94 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_9 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0160_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_dpot_95 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_7 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0153_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_dpot_98 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_6 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0153_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_dpot_99 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_8 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0153_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_dpot_100 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_4 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0160_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_dpot_96 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_3 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0160_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_dpot_97 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_5 )
  );
  FDE #(
    .INIT ( 1'b0 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7  (
    .C(clk_BUFGP_0),
    .CE(\UART_TOP_INST/UART_RX_INST/_n0153_inv1 ),
    .D(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_dpot_101 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_2 )
  );
  LUT6 #(
    .INIT ( 64'h0880808080808080 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009551  (
    .I0(\UART_TOP_INST/UART_TX_INST/Mmux__n009511 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [5])
  );
  LUT6 #(
    .INIT ( 64'h5757577757775777 ))
  \UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o11  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [5]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .O(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o )
  );
  LUT3 #(
    .INIT ( 8'h9A ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2-In1  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .O(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2-In )
  );
  LUT3 #(
    .INIT ( 8'h28 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n012121  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [1]),
    .O(\UART_TOP_INST/UART_TX_INST/_n0121 [2])
  );
  LUT4 #(
    .INIT ( 16'h0111 ))
  \UART_TOP_INST/UART_TX_INST/_n0135_inv1  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1_46 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .O(\UART_TOP_INST/UART_TX_INST/_n0135_inv )
  );
  LUT4 #(
    .INIT ( 16'h2888 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n012111  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [2]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [1]),
    .O(\UART_TOP_INST/UART_TX_INST/_n0121 [1])
  );
  LUT3 #(
    .INIT ( 8'h40 ))
  \UART_TOP_INST/UART_TX_INST/_n0085_inv11  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .O(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1-In )
  );
  LUT4 #(
    .INIT ( 16'h0100 ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In11  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1_46 ),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .O(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 )
  );
  LUT4 #(
    .INIT ( 16'h7FFF ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n0095411  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .O(\UART_TOP_INST/UART_TX_INST/Mmux__n009541 )
  );
  LUT2 #(
    .INIT ( 4'hE ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n0095111  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .O(\UART_TOP_INST/UART_TX_INST/Mmux__n009511 )
  );
  LUT2 #(
    .INIT ( 4'h2 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n012131  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0]),
    .O(\UART_TOP_INST/UART_TX_INST/_n0121 [3])
  );
  LUT6 #(
    .INIT ( 64'h8000000000000000 ))
  \UART_TOP_INST/UART_RX_INST/Madd_r_Clock_Count[7]_GND_3_o_add_23_OUT_cy<5>11  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .O(\UART_TOP_INST/UART_RX_INST/Madd_r_Clock_Count[7]_GND_3_o_add_23_OUT_cy<5> )
  );
  LUT4 #(
    .INIT ( 16'h6C00 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n013512  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I2(\UART_TOP_INST/UART_RX_INST/Madd_r_Clock_Count[7]_GND_3_o_add_23_OUT_cy<5> ),
    .I3(\UART_TOP_INST/UART_RX_INST/Mmux__n013511 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [1])
  );
  LUT2 #(
    .INIT ( 4'h8 ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In_SW0  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [1]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [0]),
    .O(N4)
  );
  LUT6 #(
    .INIT ( 64'hFFFFFFFFCCCC2000 ))
  \UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [2]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I3(N4),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I5(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In1 ),
    .O(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3-In_29 )
  );
  LUT2 #(
    .INIT ( 4'h8 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n01353_SW0  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .O(N6)
  );
  LUT6 #(
    .INIT ( 64'h6AAAAAAA00000000 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n01353  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I4(N6),
    .I5(\UART_TOP_INST/UART_RX_INST/Mmux__n013511 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [3])
  );
  LUT6 #(
    .INIT ( 64'h5757575F575F575F ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o11  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 )
  );
  LUT2 #(
    .INIT ( 4'h4 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o12  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o )
  );
  LUT6 #(
    .INIT ( 64'hAAABFFAB00015501 ))
  \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3-In  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I4(\UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o ),
    .I5(N8),
    .O(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3-In_72 )
  );
  LUT3 #(
    .INIT ( 8'hFE ))
  \UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o<7>_SW0  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .O(N10)
  );
  LUT6 #(
    .INIT ( 64'h0000000040000000 ))
  \UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o<7>  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I5(N10),
    .O(\UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o )
  );
  IBUF   rx_serial_IBUF (
    .I(rx_serial),
    .O(rx_serial_IBUF_1)
  );
  OBUF   tx_serial_OBUF (
    .I(\UART_TOP_INST/UART_TX_INST/o_Tx_Serial_11 ),
    .O(tx_serial)
  );
  LUT6 #(
    .INIT ( 64'h50A054A800000408 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n013521  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I3(\UART_TOP_INST/UART_RX_INST/Madd_r_Clock_Count[7]_GND_3_o_add_23_OUT_cy<5> ),
    .I4(\UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o ),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [2])
  );
  LUT6 #(
    .INIT ( 64'h0010000000100010 ))
  \UART_TOP_INST/UART_RX_INST/_n0160_inv11  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0160_inv1 )
  );
  LUT6 #(
    .INIT ( 64'h0020000000200020 ))
  \UART_TOP_INST/UART_RX_INST/_n0153_inv11  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0153_inv1 )
  );
  LUT6 #(
    .INIT ( 64'h0080FF0000800080 ))
  \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3-In_SW0  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(N8)
  );
  LUT5 #(
    .INIT ( 32'h00008000 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW0  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .O(N12)
  );
  LUT6 #(
    .INIT ( 64'h2E2E0C2E22220022 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I3(N12),
    .I4(N10),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/Mmux__n013511 )
  );
  LUT4 #(
    .INIT ( 16'h8088 ))
  \UART_TOP_INST/UART_RX_INST/_n0133_inv21  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1-In )
  );
  LUT5 #(
    .INIT ( 32'h00008000 ))
  \UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o<7>_SW1  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I4(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .O(N14)
  );
  LUT6 #(
    .INIT ( 64'h3333333333133333 ))
  \UART_TOP_INST/UART_RX_INST/_n0146_inv1  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I4(N14),
    .I5(N10),
    .O(\UART_TOP_INST/UART_RX_INST/_n0146_inv )
  );
  LUT5 #(
    .INIT ( 32'hC2E0C2C2 ))
  \UART_TOP_INST/UART_RX_INST/r_Bit_Index_0_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Bit_Index_0_dpot_104 )
  );
  LUT6 #(
    .INIT ( 64'hF028F028F0A0F028 ))
  \UART_TOP_INST/UART_RX_INST/r_Bit_Index_1_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .O(\UART_TOP_INST/UART_RX_INST/r_Bit_Index_1_dpot_105 )
  );
  LUT2 #(
    .INIT ( 4'h7 ))
  \UART_TOP_INST/UART_RX_INST/_n0219_inv1_rstpot_SW0  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [0]),
    .O(N18)
  );
  LUT6 #(
    .INIT ( 64'hE0C2E0E0E0C2E0C2 ))
  \UART_TOP_INST/UART_RX_INST/r_Bit_Index_2_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(N18),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Bit_Index_2_dpot_106 )
  );
  LUT6 #(
    .INIT ( 64'hFFFFDFFFFFFFFFFF ))
  \UART_TOP_INST/UART_RX_INST/GND_3_o_GND_3_o_equal_5_o<7>_SW2  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .O(N20)
  );
  LUT6 #(
    .INIT ( 64'h4C4C4C6E44444466 ))
  \UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2-In1  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I3(N10),
    .I4(N20),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2-In )
  );
  LUT6 #(
    .INIT ( 64'h9DDDDDDDDDDDDDDD ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009531_SW0  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .O(N22)
  );
  LUT6 #(
    .INIT ( 64'h1555555555555555 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009531_SW1  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .O(N23)
  );
  LUT6 #(
    .INIT ( 64'h0404040015151500 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009531  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_TX_INST/Mmux__n009541 ),
    .I2(N23),
    .I3(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I4(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I5(N22),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [3])
  );
  LUT6 #(
    .INIT ( 64'hAA80AA80AA80FFFF ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n00952_SW1  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I5(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .O(N25)
  );
  LUT6 #(
    .INIT ( 64'h95555555FFFFFFFF ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW1  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .O(N28)
  );
  LUT6 #(
    .INIT ( 64'hFFFFFFFF95555555 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW2  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .O(N29)
  );
  LUT6 #(
    .INIT ( 64'h0405AEAF04050405 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n013541  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(N10),
    .I2(N28),
    .I3(N12),
    .I4(N29),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [4])
  );
  LUT5 #(
    .INIT ( 32'h9555FFFF ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW3  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .O(N31)
  );
  LUT5 #(
    .INIT ( 32'hFFFF9555 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW4  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .O(N32)
  );
  LUT6 #(
    .INIT ( 64'h0405AEAF04050405 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n013551  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(N10),
    .I2(N31),
    .I3(N12),
    .I4(N32),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [5])
  );
  LUT4 #(
    .INIT ( 16'h95FF ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW5  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .O(N34)
  );
  LUT4 #(
    .INIT ( 16'hFF87 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n0135111_SW6  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .O(N35)
  );
  LUT6 #(
    .INIT ( 64'h10BA11BB10101111 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n013561  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I1(N34),
    .I2(N10),
    .I3(N35),
    .I4(N12),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [6])
  );
  LUT5 #(
    .INIT ( 32'hAAAAFD75 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n008811  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Bit_Index [2]),
    .I2(\UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_4_16 ),
    .I3(\UART_TOP_INST/UART_TX_INST/Mmux_r_Bit_Index[2]_r_Tx_Data[7]_Mux_8_o_3_15 ),
    .I4(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .O(\UART_TOP_INST/UART_TX_INST/_n0088 )
  );
  LUT4 #(
    .INIT ( 16'hABA8 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_9 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_0_dpot_94 )
  );
  LUT4 #(
    .INIT ( 16'hAEA2 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_7 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_2_dpot_95 )
  );
  LUT4 #(
    .INIT ( 16'hEA2A ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_3 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_6_dpot_96 )
  );
  LUT4 #(
    .INIT ( 16'hAEA2 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_5 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_4_dpot_97 )
  );
  LUT4 #(
    .INIT ( 16'hAEA2 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_6 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_3_dpot_98 )
  );
  LUT4 #(
    .INIT ( 16'hABA8 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_8 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_1_dpot_99 )
  );
  LUT4 #(
    .INIT ( 16'hAEA2 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_4 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_5_dpot_100 )
  );
  LUT4 #(
    .INIT ( 16'hEA2A ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_2 ),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Bit_Index [2]),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Rx_Byte_7_dpot_101 )
  );
  LUT6 #(
    .INIT ( 64'h7F7F7FFFFFFFFFFF ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n00952_SW3  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I4(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .O(N40)
  );
  LUT5 #(
    .INIT ( 32'h00402262 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n00952  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [6]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [5]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4]),
    .I3(N40),
    .I4(N25),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [2])
  );
  LUT4 #(
    .INIT ( 16'h8000 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009542_SW0  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [3]),
    .O(N42)
  );
  LUT6 #(
    .INIT ( 64'hFCA8540000000000 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009542  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [4]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I3(N42),
    .I4(\UART_TOP_INST/UART_TX_INST/Mmux__n009541 ),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [4])
  );
  LUT6 #(
    .INIT ( 64'h0060666000600060 ))
  \UART_TOP_INST/UART_RX_INST/Mmux__n013571  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I3(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I5(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0135 [7])
  );
  LUT5 #(
    .INIT ( 32'h00E0E000 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009571  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [7])
  );
  LUT6 #(
    .INIT ( 64'h00E0E000E000E000 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009561  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I1(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I3(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [2]),
    .I4(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I5(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [1]),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [6])
  );
  LUT4 #(
    .INIT ( 16'h4440 ))
  \UART_TOP_INST/UART_TX_INST/Mmux__n009581  (
    .I0(\UART_TOP_INST/UART_TX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_TX_INST/r_Clock_Count[7]_GND_4_o_LessThan_19_o ),
    .I2(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd3_44 ),
    .I3(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd2_45 ),
    .O(\UART_TOP_INST/UART_TX_INST/_n0095 [8])
  );
  LUT5 #(
    .INIT ( 32'hFFF7FFFF ))
  \UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [5]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I2(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I3(N10),
    .I4(N14),
    .O(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 )
  );
  LUT3 #(
    .INIT ( 8'hE2 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_1_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [1]),
    .I1(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 ),
    .I2(\UART_TOP_INST/UART_RX_INST/_n0135 [7]),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_1_dpot_124 )
  );
  LUT3 #(
    .INIT ( 8'hE2 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_2_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [2]),
    .I1(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 ),
    .I2(\UART_TOP_INST/UART_RX_INST/_n0135 [6]),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_2_dpot_125 )
  );
  LUT3 #(
    .INIT ( 8'hE2 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_3_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [3]),
    .I1(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 ),
    .I2(\UART_TOP_INST/UART_RX_INST/_n0135 [5]),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_3_dpot_126 )
  );
  LUT3 #(
    .INIT ( 8'hE2 ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_4_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [4]),
    .I1(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 ),
    .I2(\UART_TOP_INST/UART_RX_INST/_n0135 [4]),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_4_dpot_127 )
  );
  LUT6 #(
    .INIT ( 64'h04540404AAAAAAAA ))
  \UART_TOP_INST/UART_RX_INST/r_Clock_Count_0_dpot  (
    .I0(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [0]),
    .I1(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .I2(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd2_84 ),
    .I3(\UART_TOP_INST/UART_RX_INST/r_Clock_Count [7]),
    .I4(\UART_TOP_INST/UART_RX_INST/r_Clock_Count[7]_GND_3_o_LessThan_23_o1 ),
    .I5(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_rstpot_121 ),
    .O(\UART_TOP_INST/UART_RX_INST/r_Clock_Count_0_dpot_123 )
  );
  BUFGP   clk_BUFGP (
    .I(clk),
    .O(clk_BUFGP_0)
  );
  INV   \UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv1_INV_0  (
    .I(\UART_TOP_INST/UART_TX_INST/r_SM_Main_FSM_FFd1_46 ),
    .O(\UART_TOP_INST/UART_TX_INST/r_SM_Main<2>_inv )
  );
  INV   \UART_TOP_INST/UART_RX_INST/_n0219_inv1_cepot_INV_0  (
    .I(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd3_83 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0219_inv1_cepot )
  );
  INV   \UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot_INV_0  (
    .I(\UART_TOP_INST/UART_RX_INST/r_SM_Main_FSM_FFd1_10 ),
    .O(\UART_TOP_INST/UART_RX_INST/_n0146_inv1_cepot )
  );
  GND   XST_GND (
    .G(N44)
  );
  VCC   XST_VCC (
    .P(N45)
  );
  SRLC16E #(
    .INIT ( 16'h0001 ))
  \UART_TOP_INST/UART_RX_INST/Mshreg_r_Rx_Data  (
    .A0(N44),
    .A1(N44),
    .A2(N44),
    .A3(N44),
    .CE(N45),
    .CLK(clk_BUFGP_0),
    .D(rx_serial_IBUF_1),
    .Q(\UART_TOP_INST/UART_RX_INST/Mshreg_r_Rx_Data_130 ),
    .Q15(\NLW_UART_TOP_INST/UART_RX_INST/Mshreg_r_Rx_Data_Q15_UNCONNECTED )
  );
  FDE #(
    .INIT ( 1'b1 ))
  \UART_TOP_INST/UART_RX_INST/r_Rx_Data  (
    .C(clk_BUFGP_0),
    .CE(N45),
    .D(\UART_TOP_INST/UART_RX_INST/Mshreg_r_Rx_Data_130 ),
    .Q(\UART_TOP_INST/UART_RX_INST/r_Rx_Data_85 )
  );
endmodule


`ifndef GLBL
`define GLBL

`timescale  1 ps / 1 ps

module glbl ();

    parameter ROC_WIDTH = 100000;
    parameter TOC_WIDTH = 0;

//--------   STARTUP Globals --------------
    wire GSR;
    wire GTS;
    wire GWE;
    wire PRLD;
    tri1 p_up_tmp;
    tri (weak1, strong0) PLL_LOCKG = p_up_tmp;

    wire PROGB_GLBL;
    wire CCLKO_GLBL;

    reg GSR_int;
    reg GTS_int;
    reg PRLD_int;

//--------   JTAG Globals --------------
    wire JTAG_TDO_GLBL;
    wire JTAG_TCK_GLBL;
    wire JTAG_TDI_GLBL;
    wire JTAG_TMS_GLBL;
    wire JTAG_TRST_GLBL;

    reg JTAG_CAPTURE_GLBL;
    reg JTAG_RESET_GLBL;
    reg JTAG_SHIFT_GLBL;
    reg JTAG_UPDATE_GLBL;
    reg JTAG_RUNTEST_GLBL;

    reg JTAG_SEL1_GLBL = 0;
    reg JTAG_SEL2_GLBL = 0 ;
    reg JTAG_SEL3_GLBL = 0;
    reg JTAG_SEL4_GLBL = 0;

    reg JTAG_USER_TDO1_GLBL = 1'bz;
    reg JTAG_USER_TDO2_GLBL = 1'bz;
    reg JTAG_USER_TDO3_GLBL = 1'bz;
    reg JTAG_USER_TDO4_GLBL = 1'bz;

    assign (weak1, weak0) GSR = GSR_int;
    assign (weak1, weak0) GTS = GTS_int;
    assign (weak1, weak0) PRLD = PRLD_int;

    initial begin
	GSR_int = 1'b1;
	PRLD_int = 1'b1;
	#(ROC_WIDTH)
	GSR_int = 1'b0;
	PRLD_int = 1'b0;
    end

    initial begin
	GTS_int = 1'b1;
	#(TOC_WIDTH)
	GTS_int = 1'b0;
    end

endmodule

`endif

