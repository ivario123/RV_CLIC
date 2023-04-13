///////////////////////////////////////////////////////////////////////////////////////////
//                                                                                       //       
//  Defines a generic block of registers                                                 //
//  Each register is spaced by REG_SPACING bytes                                         //
//  and addressable by the first byte of the register                                    //
//                                                                                       //
//  Parameters:                                                                          //
//    DATA_WIDTH: Width of the data bus                                                  //
//    ADDRESS_WIDTH: Width of the address bus                                            //
//    REGISTERS: Number of registers in the block                                        //
//    START_ADDRESS: Address of the first register                                       //
//    REG_SPACING: Spacing between registers                                             //
//    END_ADDRESS: Address of the last register                                          //
//                                                                                       //
//  Inputs:                                                                              //
//    clock: Clock signal                                                                //
//    reset: Reset signal                                                                //
//    address: Address of the register to read/write                                     //
//    write_enable: Write enable signal                                                  //
//    write_data: Data to write to the register                                          //
//                                                                                       //
//  Outputs:                                                                             //
//    read_data: Data read from the register                                             //
//                                                                                       //
///////////////////////////////////////////////////////////////////////////////////////////

enum logic [1:0] {
  READ_ONLY,
  WRITE_ONLY,
  READ_WRITE
} PERMISSIONS;

module REGBLOCK #(
    parameter DATA_WIDTH = 32,
    parameter ADDRESS_WIDTH = 32,
    parameter REGISTERS = 256,
    parameter START_ADDRESS = 0,
    parameter REG_SPACING = 1,
    parameter END_ADDRESS = START_ADDRESS + REG_SPACING * DATA_WIDTH * (REGISTERS - 1),
    parameter DEFAULT_VALUE = 0,
    parameter ACCESS_TYPE = READ_WRITE
) (
    input clock,
    input reset,
    input [ADDRESS_WIDTH-1:0] address,
    input write_enable,
    input [DATA_WIDTH-1:0] write_data,
    output reg [DATA_WIDTH-1:0] read_data,
    output reg [DATA_WIDTH-1:0] registers[REGISTERS-1:0]
);
  initial begin
    for (int i = 0; i < REGISTERS; i++) begin
      registers[i] <= DEFAULT_VALUE;
    end
  end


  always @(posedge clock) begin
    int read;
    case (reset)
      1'b1: begin
        // Connect the read data to ground
        read = 0;
        for (int i = 0; i < REGISTERS; i++) begin
          // Set all registers to 0 if reset is high
          registers[i] <= 32'b0;
        end
      end
      1'b0: begin
        // Do bounds checking on the address and make sure it is aligned
        if (address >= START_ADDRESS && address <= END_ADDRESS && (address-START_ADDRESS) % (REG_SPACING*DATA_WIDTH) == 0) begin
          if (write_enable && ACCESS_TYPE != READ_ONLY) 
            // Write data to the register file if write enable is high
            registers[(address-START_ADDRESS)/REG_SPACING] <= write_data;
          // Set the new read data
          read = registers[(address-START_ADDRESS)/REG_SPACING];
        end else begin
          // If address is out of bounds, read the previous value
          read = read_data;
        end
      end
    endcase
    if (ACCESS_TYPE != WRITE_ONLY) read_data <= read;
  end



endmodule
