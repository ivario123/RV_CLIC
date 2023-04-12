module REGBLOCK #(
    parameter DATA_WIDTH = 32,
    parameter ADDRESS_WIDTH = 32,
    parameter REGISTERS = 256,
    parameter START_ADDRESS = 0,
    parameter REG_SPACING = 4,
    parameter END_ADDRESS = START_ADDRESS + (REGISTERS * REG_SPACING) - 1

) (
    input clock,
    input reset,
    input [ADDRESS_WIDTH-1:0] address,
    input write_enable,
    input [DATA_WIDTH-1:0] write_data,
    output reg [DATA_WIDTH-1:0] read_data,
    output reg [DATA_WIDTH-1:0] registers[REGISTERS-1:0]
);


  always @(posedge clock) begin
    int read;
    if (reset) begin
      read = 0;
      // Reset all registers to 0
      for (int i = 0; i < REGISTERS; i++) begin
        registers[i] <= 0;
      end
    end else begin
      // Check that address is within the range of the register file
      if (address < START_ADDRESS || address > END_ADDRESS) begin
        read = read_data;
      end else begin
        // Now we can continue with the operations

        // Handle write enable
        if (write_enable) begin
          registers[(address-START_ADDRESS)/REG_SPACING] <= write_data;
        end

        // Read data from the register file
        read = registers[address];
      end
    end
    read_data <= read;
  end



endmodule
