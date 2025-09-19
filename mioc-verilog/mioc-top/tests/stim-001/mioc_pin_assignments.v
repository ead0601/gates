
   // OUTPUT ASSIGNMENTS
   //
   assign RA7           = w_u23z;   //: pin 2 : (goes to U9 , RAM Address 7.This is the multiplexed RAM address MSB.)	       
   assign BUSRQ_N       = w_u86z;   //: pin18 : Active low bus request
   assign SPINDIS_N     = w_u88qb;  //: pin19 : Active low Controller Spinner Interrupt Disable
   assign NETRST_N      = w_u90qb;   //: pin20 : Active low - Reset for AdamNET
   assign AUXDECODE1_N  = w_u42z;   //: pin 22 : Active low - Disables the onboard mem decode on CV board?
   assign RST_N         = w_u53z;   //: pin 23 : Active low reset - System Reset circuitry
   assign CPRST_N       = w_u94z;   //: pin 24 : Active low reset - not used
   assign AUXROMCS_N    = w_u48z;   //: pin 26 : Active low aux rom chip select - Slot 2 Expansion ROM CS
   assign ADDRBUFEN_N   = w_u50z;   //: pin 27 : Active low address buffer enable - according to earlier docs, enables/disables
                                    //:     /BRFSH, /BMREQ, /BM1, and /BIORQ (disabled during DMA cycle)
   assign BOOTROMCS_N   = w_u76z;   //: pin 28 : Active low boot ROM chip select - For Smartwriter ROM
   assign EN245_N       = w_u79z;   //: pin 29 : Active low 245 enable - CV onboard decode enable/disable?
   assign IS3_N         = w_u63z;   //: pin 30 : Active low IS3 To Master 6801
   assign MUX           = w_u14qb;  //: pin 37 : Output Mux signal for memory address signals for DRAM.
   assign RAS_N         = w_u49z;   //: pin 38 : Active low row address strobe
   assign CAS1_N        = w_u9z;    //: pin 39 : Active low column address strobe 1
   assign CAS2_N        = w_u8z;    //: pin 40 : Active low column address strobe 2

   // INPUT ASSIGNMENTS 
   //   
   // IOPADS have two outputs each: BUF = INV + INV , so either the buffered or inverted signal is used.
   //
   assign  PIN_IN_3    = ~BA15      ; //: pin 3 : Address line 15
   assign  PIN_IN_4    = ~BA14      ; //: pin 4 : Address line 14
   assign  PIN_IN_5    = ~BA13      ; //: pin 5 : Address line 13
   assign  PIN_IN_6    = N_CVRST   ; //: pin 6 : Active low reset signal “Game Reset”
   assign  PIN_IN_7    = ~BD0       ; //: pin 7 : Data line 0
   assign  PIN_IN_8    = ~BD1       ; //: pin 8 : Data line 1
   assign  PIN_IN_9    = ~BD2       ; //: pin 9 : Data line 2
   assign  PIN_IN_10   = ~BD3       ; //: pin10 : Data line 3
   assign  PIN_IN_11   = ~N_BWR     ; //: pin11 : Active low write signal Buffered Write (according to earlier docs, gated by MA5,/IORQ, and A10
   assign  PIN_IN_12   = ~BA6       ; //: pin12 : Address line 6

   assign  PIN_IN_13   = BA7       ; //: pin13 : Address line 7 (according to earlier docs, gated by /ADDRBUFEN)
   assign  PIN_IN_13N  = ~BA7      ; //: INVERTED pin13 : Address line 7 (according to earlier docs, gated by /ADDRBUFEN)

   assign  PIN_IN_14   = IORQ_N    ; //: pin14 : Active low Z80 IO Request
   assign  PIN_IN_15   = WAIT_N    ; //: pin15 : Active low wait signal, Memory wait state
   assign  PIN_IN_16   = BUSAK_N   ; //: pin16 : Active low bus acknowledge - Z80 Control
   assign  PIN_IN_17   = DMA_N     ; //: pin17 : Active low DMA transaction asserted by 6801 to signal DMA to RAM
   assign  PIN_IN_25   = ~PBRST_N   ; //: pin 25 : Active low ADAM Reset switch for computer mode

   assign  PIN_IN_31   = ~OS3_N     ; //: pin 31 : Active low OS3 From Master 6801
   assign  PIN_IN_32   = ~BMREQ_N   ; //: pin 32 : Active low Buffered Memory Request
   assign  PIN_IN_33   = ~BRD_N     ; //: pin 33 : Active low Buffered Memory Read
   assign  PIN_IN_34   = BRFSH_N   ; //: pin 34 : Active low Buffered Memory Refresh
   assign  PIN_IN_35   = ~BM1_N     ; //: pin 35 : Active low Buffered M1, indicates M1 Z80 is in M1 state.
   assign  PIN_IN_36   = B_PHI     ; //: pin 36 : Z80 Clock
