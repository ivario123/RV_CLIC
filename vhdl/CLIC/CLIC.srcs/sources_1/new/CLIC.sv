///////////////////////////////////////////////////////////////////////////////////////////
//                                                                                       //                               
//  Implementation of the Core Local Interrupt Controller (CLIC) for a generic           //
//  RISC-V core.                                                                         //
//                                                                                       //               
///////////////////////////////////////////////////////////////////////////////////////////

module CLIC #(

) (
    clock,
    reset,
    write_data,
    write_enable,
    read
);
  input clock;
  input reset;
  input write_enable;
  input [31:0] write_data;
  output reg [31:0] read;

  // Directly connected to the memory
  reg [31:0] internal_read_address;
  reg [31:0] internal_read_data;
  // Register file
  // Inputs lock, address, write_enable, write_data, read_data, internal_read_address,internal_read_data
  REGFILE memory (
      .clock(clock),
      .reset(reset),
      .write_enable(write_enable),
      .write_data(write_data),
      .read_data(read)
  );

  always @(posedge clock) begin
    // This will do all of the logic for the CLIC
  end



endmodule
;
