module clicintattr #(
    parameter SOURCES = 256,
    parameter ADDRESS_WIDTH = 32
) (
    input clock,
    input reset,
    input [ADDRESS_WIDTH-1:0] address,
    input [7:0] write_data_in,
    input write_enable,
    input [1:0] mode,
    output [7:0] read_data,
    output [7:0] registers[SOURCES-1:0]

);

  reg [7:0] write_data_out;

  REGBLOCK #(
      .DATA_WIDTH(8),
      .ADDRESS_WIDTH(32),
      .REGISTERS(SOURCES),
      .START_ADDRESS(32'h1002),
      .REG_SPACING(4)
  ) clicintattr_internal (
      .clock(clock),
      .reset(reset),
      .address(address),
      .write_enable(write_enable),
      .write_data(write_data_out),
      .read_data(read_data),
      .registers(registers)
  );

  initial begin
    $display("clicintattr: %d sources, %d address bits", SOURCES, ADDRESS_WIDTH);
  end
  always_comb begin
    // Pull all reserved signals to gnd
    write_data_out[5:3] <= 3'b000;  // reserved
    write_data_out[0]   <= 1'b0;  // reserved
  end

endmodule


