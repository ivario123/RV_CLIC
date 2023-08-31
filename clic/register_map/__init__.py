from os import write
from helpers import decorators
from helpers.decorators import simulation, test, simulator
from .registerfile import *
from .registermap import *
from amaranth import Elaboratable, Module, Signal, Memory, Mux, Cat
from amaranth.sim import Simulator
from amaranth.sim import Settle, Tick


@simulator
def sim():
    register_file = RegisterFile(
        register_count=120,
        register_width=32,
        register_type=RegisterType.READ_WRITE,
        valid=lambda _: True,
        initial_values=lambda _: 0x00000000,
        start_address=0x04,
        file_name="Register file",
        file_description="Register file description",
    )

    registermap = RegisterMap()

    @simulation(registerfile=register_file)
    def reg_file():
        @test
        def write_all_read_all():
            """
            Writes to every register in the register file. 

            Tests:
                - Write
                - Read
                - Decoupling
            """
            for i in range(registerfile.register_count):
                yield registerfile.write_enable.eq(1)
                yield registerfile.address.eq(
                    i * registerfile.register_width + registerfile.start_address
                )
                yield registerfile.write_data.eq(i + 1)
                yield Tick()
                yield registerfile.write_enable.eq(0)
                yield Tick()
                assert (yield registerfile._out_of_bounds) == 0
                assert (yield registerfile.read_data) == i + 1

        @test
        def address_out_of_bounds():
            """
            Writes to a too large address
            
            Tests:
                - Bounds checking
            """
            yield registerfile.address.eq(
                registerfile.register_count * registerfile.register_width
                + 400 * registerfile.register_width
                + registerfile.start_address
            )
            yield registerfile.write_enable.eq(1)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            yield registerfile.write_enable.eq(0)
            yield Tick()
            assert (yield registerfile._out_of_bounds) == 1
            assert (yield registerfile.read_data) == 0x0

        @test
        def to_small_address():
            """
            Writes to an address that is not in the register.
            
            Tests:
                - Bounds checking
            """
            yield registerfile.address.eq(0x00)
            yield registerfile.write_enable.eq(1)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            yield registerfile.write_enable.eq(0)
            yield Tick()
            assert (yield registerfile.read_data) == 0x0

        @test
        def register_file():
            """
            Writes to the first register and reads the data from it.
            
            Tests:
                - Basic instantiation
                - Basic Read/Write
            """
            yield registerfile.write_enable.eq(1)
            yield registerfile.address.eq(0x00 + registerfile.start_address)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            yield registerfile.write_enable.eq(0)
            yield Tick()
            assert (yield registerfile.read_data) == 0x0000111

        @test
        def write_to_2_read_from_3():
            """
            Writes from reg nr 2 in the file
            reads from reg nr 2 i.e. 0x04 
            reads from register nr 3 i.e. 0x08 

            Tests:
                - Basic read/write
                - Decoupling
            """
            yield registerfile.write_enable.eq(1)
            yield registerfile.address.eq(0x04 + registerfile.start_address)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            yield registerfile.write_enable.eq(0)
            print(f"Register 2 value: {(yield registerfile.read_data)}")
            yield registerfile.address.eq(0x08 + registerfile.start_address)
            yield Tick()
            print(f"Register 3 value: {(yield registerfile.read_data)}")
            assert (yield registerfile.read_data) == 0x0

    @simulation(registermap=registermap)
    def reg_map():
        @test
        def register_map():
            """
            Writes and reads from a single register
            
            Tests:
                - Basic instantiation
                - Basic Write
                - Basic Read
            """
            working_register = registermap.BaseAddresses.CLICINTTRIG
            value_to_write = 15
            yield registermap.address.eq(working_register)
            yield registermap.write_enable.eq(1)
            yield registermap.write_data.eq(value_to_write)
            yield Tick()
            yield registermap.write_enable.eq(0)
            yield Tick()
            print(f"Register 0 value: {(yield registermap.read_data)}")
            assert (yield registermap.read_data) == 15

        @test
        def write_all_read_all():
            """
            Writes to all register files in order. 
            Tests:
                - Write
                - Read
            """
            for i, reg in enumerate(registermap.write_able_addresses):
                write_value = i + 1
                print(f"Register {reg.name} @0x{reg.value:x}")
                yield registermap.address.eq(reg)
                yield registermap.write_enable.eq(1)
                yield registermap.write_data.eq(write_value)
                yield Tick()
                yield registermap.write_enable.eq(0)
                yield Tick()
                print(f"internal_address = {(yield registermap.address)}")
                print(
                    f"Register {reg.name} value: {(yield registermap.read_data)} should be {write_value}"
                )
                if (yield registermap.is_quad_mapped):
                    print("Register is quad mapped")

                assert (yield registermap.read_data) == write_value

                # assert (yield registermap.read_data) == i

        @test
        def write_to_one_read_from_all():
            """
            Writes to every register file and then asserts that no other register files
            reflect that same change. Resets register bank inbetween writes.

            Tests:
                - Write
                - Read
                - Decoupling
                - Reset functionallity
            """
            for reg in registermap.write_able_addresses:
                for reg in registermap.write_able_addresses:
                    yield registermap.reset.eq(1)
                    yield registermap.address.eq(reg)
                    yield Tick()
                    yield registermap.reset.eq(0)
                write_val = 1
                # Write the data to reg
                yield registermap.address.eq(reg)
                yield registermap.write_enable.eq(1)
                yield registermap.write_data.eq(write_val)
                yield Tick()
                # Dissable writing
                yield registermap.write_enable.eq(0)
                yield Tick()
                yield Tick()
                # print(f"{reg.name} Read val : {(yield registermap.read_data)}")

                # Value should now be in reg but no other reg, go over the registers, read all registers
                # If no other register but reg has the correct value, go on to the next one.
                for read_reg in registermap.write_able_addresses:
                    yield registermap.address.eq(read_reg)
                    yield Tick()

                    if reg.name == read_reg.name:
                        if (yield registermap.read_data) != write_val:
                            print(
                                f"""
        Internal state:
                - write_reg {reg.name}
                - read_reg {read_reg.name}
                - expected value {write_val}
                - addr 0x{(yield registermap.address):x}
                - reg 0b{(yield registermap.reg):b}
                - intermediate_addr {(yield registermap.address_intermediate)}
                - is_quad_mapped {(yield registermap.is_quad_mapped)}
                - lsbs {(yield registermap.lsbs)}
                                      """
                            )
                        assert (yield registermap.read_data) == write_val
                    else:
                        if (yield registermap.read_data) == write_val:
                            print(
                                f"""
        Internal state:
                - write_reg {reg.name}
                - read_reg {read_reg.name}
                - expected value {write_val}
                - addr 0x{(yield registermap.address):x}
                - reg 0b{(yield registermap.reg):b}
                - intermediate_addr {(yield registermap.address_intermediate)}
                - is_quad_mapped {(yield registermap.is_quad_mapped)}
                - lsbs {(yield registermap.lsbs)}
                                      """
                            )
                        assert (yield registermap.read_data) != write_val

            for reg in registermap.write_able_addresses:
                yield registermap.reset.eq(1)
                yield registermap.address.eq(reg)
                yield Tick()
                print(f"{reg.name} value after reset {(yield registermap.read_data)}")

    reg_file()
    reg_map()
