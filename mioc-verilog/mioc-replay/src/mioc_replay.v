`timescale 1ns/1ps
// ============================================================================
// Auto-fixed vector replay module (DDR both-edge stepping)
// Generated from /mnt/data/mioc-replay.v by ChatGPT on request
// Notes:
//  - Verilog-2001 compatible (no SystemVerilog types; no $fatal).
//  - Bit 0 of the input vector is treated as BPHI per recovered mapping.
//  - OUT_VEC_WIDTH must be >= 1 for comparison logic as written.
// ============================================================================

// ------------------------- defaults (override via `define) -------------------
`ifndef VEC_IN_FILE
  `define VEC_IN_FILE  "./DATA_IN/inputs_both_edges.mem"
`endif
`ifndef VEC_OUT_FILE
  `define VEC_OUT_FILE "./DATA_IN/outputs_both_edges.mem"
`endif
`ifndef IN_VEC_WIDTH
  `define IN_VEC_WIDTH 30
`endif
`ifndef OUT_VEC_WIDTH
  `define OUT_VEC_WIDTH 15
`endif
`ifndef VEC_DEPTH
  `define VEC_DEPTH 1024
`endif
`ifndef VEC_WAIT_EDGES
  `define VEC_WAIT_EDGES 10
`endif
// ----------------------------------------------------------------------------

module mioc_replay (
    input wire clk,
    input wire reset_n,

    // Pins driven into DUT (from vectors):
    output     BPHI,
    output     BA15,
    output     BA14,
    output     BA13,
    output     nCVRST,
    output     BD0,
    output     BD1,
    output     BD2,
    output     BD3,
    output     nBWR,
    output     BA6,
    output     BA7,
    output     nIORQ,
    output     nWAIT,
    output     nBUSAK,
    output     nDMA,
    output     nCPRST,
    output     nPBRST,
    output     nOS3,
    output     nBMREQ,
    output     nBRD,
    output     nBRFSH,
    output     nBM1,
			  
    // Pins captured from DUT (to compare):
    input 	    RA7,
    input 	    nBUSRQ,
    input 	    nEOS_ENABLE,
    input 	    nNET_RST,
    input 	    nAUX_DECODE1,
    input 	    nRST,
    input 	    nAUX_ROM_CS,
    input 	    nADDRBUFEN,
    input 	    nBOOT_ROM_CS,
    input 	    nEN245,
    input 	    nIS3,
    input 	    MUX,
    input 	    nRAS1,
    input 	    nCAS1,
    input 	    nCAS2
    );

    // Just for simulation observation
    // LA1010 captured outputs
    wire   cap_RA7;
    wire   cap_nBUSRQ;
    wire   cap_nEOS_ENABLE;
    wire   cap_nNET_RST;
    wire   cap_nAUX_DECODE1;
    wire   cap_nRST;
    wire   cap_nAUX_ROM_CS;
    wire   cap_nADDRBUFEN;
    wire   cap_nBOOT_ROM_CS;
    wire   cap_nEN245;
    wire   cap_nIS3;
    wire   cap_MUX;
    wire   cap_nRAS1;
    wire   cap_nCAS1;
    wire   cap_nCAS2;
   
    localparam integer INW   = `IN_VEC_WIDTH;
    localparam integer OUTW  = `OUT_VEC_WIDTH;

    // Internal vectors
    reg  [INW-1:0]  stim_in_vec;    // drives DUT pins (bit0=BPHI)
    wire [OUTW-1:0] dut_out_vec;    // captures DUT pins for compare

    // File handles and temp words
    integer fdi, fdo;
    integer rc_in, rc_out;
    reg [INW-1:0]  in_word;
    reg [OUTW-1:0] out_word;
    integer eof_in, eof_out;

    integer waited_edges;
    integer pass_count, fail_count;

    initial begin
      fdi = $fopen(`VEC_IN_FILE, "r");
      if (fdi == 0) begin
        $display("ERROR: cannot open %s", `VEC_IN_FILE);
        $finish;
      end
      if (OUTW > 0) begin
        fdo = $fopen(`VEC_OUT_FILE, "r");
        if (fdo == 0) begin
          $display("ERROR: cannot open %s", `VEC_OUT_FILE);
          $finish;
        end
      end
      stim_in_vec  = {INW{1'b0}};
      waited_edges = 0;
      pass_count   = 0;
      fail_count   = 0;
      eof_in       = 0;
      eof_out      = (OUTW == 0) ? 1 : 0;
    end

    // Both-edge stepping with async reset
    always @(posedge clk or negedge clk or negedge reset_n) begin
      if (!reset_n) begin
        stim_in_vec  <= {INW{1'b0}};
        waited_edges <= 0;
        pass_count   <= 0;
        fail_count   <= 0;
        eof_in       <= 0;
        eof_out      <= (OUTW == 0) ? 1 : 0;
      end else begin
        if (waited_edges < `VEC_WAIT_EDGES) begin
          waited_edges <= waited_edges + 1;
          stim_in_vec  <= {INW{1'b0}};
        end else begin
          // Get next input vector if available
          if (!eof_in) begin
            rc_in = $fscanf(fdi, "%b\n", in_word);
            if (rc_in != 1) begin
              eof_in = 1;
              `ifdef VEC_VERBOSE
                $display("[%0t] EOF reached on %s", $time, `VEC_IN_FILE);
              `endif
            end else begin
              stim_in_vec <= in_word;
            end
          end

          // Compare outputs if available
          if (OUTW > 0 && !eof_out) begin
            rc_out = $fscanf(fdo, "%b\n", out_word);
            if (rc_out != 1) begin
              eof_out = 1;
              `ifdef VEC_VERBOSE
                $display("[%0t] EOF reached on %s", $time, `VEC_OUT_FILE);
              `endif
            end else begin
              if (dut_out_vec === out_word) begin
                pass_count <= pass_count + 1;
                `ifdef VEC_VERBOSE
                  `ifndef VEC_SILENT_ON_PASS
                    $display("[%0t] PASS exp=%0b got=%0b", $time, out_word, dut_out_vec);
                  `endif
                `endif
              end else begin
                fail_count <= fail_count + 1;
                $display("[%0t] FAIL exp=%0b got=%0b", $time, out_word, dut_out_vec);
                `ifdef VEC_STOP_ON_MISMATCH
                  $display("Stopping on first mismatch.");
                  $finish;
                `endif
              end
            end
          end

          // If both streams have ended, we are done
          if (eof_in && (OUTW == 0 || eof_out)) begin
            $display("[%0t] DONE (EOF streaming). pass=%0d fail=%0d",
                     $time, pass_count, fail_count);
            $finish;
          end
        end
      end
    end

   // Drive DUT pins from current stimulus vector
   assign BPHI       = stim_in_vec[2];
   assign BA15       = stim_in_vec[4];
   assign BA14       = stim_in_vec[5];
   assign BA13       = stim_in_vec[6];
   assign nCVRST     = stim_in_vec[7];
   assign BD0        = stim_in_vec[8];
   assign BD1        = stim_in_vec[9];
   assign BD2        = stim_in_vec[10];
   assign BD3        = stim_in_vec[11];
   assign nBWR       = stim_in_vec[12];
   assign BA6        = stim_in_vec[13];
   assign BA7        = stim_in_vec[14];
   assign nIORQ      = stim_in_vec[15];
   assign nWAIT      = stim_in_vec[16];
   assign nBUSAK     = stim_in_vec[17];
   assign nDMA       = stim_in_vec[18];
   assign nCPRST     = stim_in_vec[19];
   assign nPBRST     = stim_in_vec[20];
   assign nOS3       = stim_in_vec[21];
   assign nBMREQ     = stim_in_vec[22];
   assign nBRD       = stim_in_vec[23];
   assign nBRFSH     = stim_in_vec[24];
   assign nBM1       = stim_in_vec[25];

   // Capture DUT outputs into compare vector
   assign dut_out_vec[0] = RA7;
   assign dut_out_vec[1] = nBUSRQ;
   assign dut_out_vec[2] = nEOS_ENABLE;
   assign dut_out_vec[3] = nNET_RST;
   assign dut_out_vec[4] = nAUX_DECODE1;
   assign dut_out_vec[5] = nRST;
   assign dut_out_vec[6] = nAUX_ROM_CS;
   assign dut_out_vec[7] = nADDRBUFEN;
   assign dut_out_vec[8] = nBOOT_ROM_CS;
   assign dut_out_vec[9] = nEN245;
   assign dut_out_vec[10] = nIS3;
   assign dut_out_vec[11] = MUX;
   assign dut_out_vec[12] = nRAS1;
   assign dut_out_vec[13] = nCAS1;
   assign dut_out_vec[14] = nCAS2;

   // LA1010 captured signals
   assign cap_RA7	    = out_word[0]; 
   assign cap_nBUSRQ	    = out_word[1]; 
   assign cap_nEOS_ENABLE   = out_word[2]; 
   assign cap_nNET_RST	    = out_word[3]; 
   assign cap_nAUX_DECODE1  = out_word[4]; 
   assign cap_nRST	    = out_word[5]; 
   assign cap_nAUX_ROM_CS   = out_word[6]; 
   assign cap_nADDRBUFEN    = out_word[7]; 
   assign cap_nBOOT_ROM_CS  = out_word[8]; 
   assign cap_nEN245	    = out_word[9]; 
   assign cap_nIS3	    = out_word[10]; 
   assign cap_MUX	    = out_word[11]; 
   assign cap_nRAS1	    = out_word[12]; 
   assign cap_nCAS1	    = out_word[13]; 
   assign cap_nCAS2         = out_word[14];  

  endmodule
