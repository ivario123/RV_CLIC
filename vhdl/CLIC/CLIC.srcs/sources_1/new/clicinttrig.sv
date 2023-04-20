module clicinttrig #(
    parameter SOURCES = 256,
    parameter ADDRESS_WIDTH = 32
) (
    input clock,
    input reset,
    input [ADDRESS_WIDTH-1:0] address,
    input [31:0] write_data_in,
    input write_enable,
    input [1:0] mode,
    output [31:0] read_data,
    output [31:0] registers[SOURCES-1:0]
);
  reg [31:0] write_data_out;
  REGBLOCK #(
      .DATA_WIDTH(32),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h0040)
  ) clicinttrig (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data_in),
      .read_data(read_data),
      .registers(registers)
  );
  initial begin
    $display("clicinttrig: %d sources, %d address bits", SOURCES, ADDRESS_WIDTH);
  end
  always_comb begin

    write_data_out[30:13] <= 0;  // reserved pulled to gnd
  end
endmodule


