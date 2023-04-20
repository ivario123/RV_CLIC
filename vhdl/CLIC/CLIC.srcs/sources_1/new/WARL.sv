`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/18/2023 10:45:55 AM
// Design Name: 
// Module Name: WARL
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


// Handles the WARL (Write Any Read Legal) behavior of the register
// WARL is a behavior of the register that allows any value to be written to it
// but only certain values can be read from it
// Functionally this means that any non legal value will be discarded and the
// legal value will be read back


module WARL #(
    parameter DATA_WIDTH = 32,
    parameter MASK = DATA_WIDTH'(1)

) (
    input  wire [DATA_WIDTH-1:0] data_in,
    output reg  [DATA_WIDTH-1:0] data_out
);

  always @(posedge clk) begin
    // If the value written to the register is legal, then write it to the register
    // If the value written to the register is not legal, then discard the value
    if (data_in & LEGAL_VALUES) begin
      data_out_reg <= data_in & MASK;  // Only keep the valid bits
    end
  end

  assign data_out = data_out_reg & MASK;
endmodule
