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
            for i in range(registerfile.register_count):
                yield registerfile.write_enable.eq(1)
                yield registerfile.address.eq(
                    i * registerfile.register_width + registerfile.start_address
                )
                yield registerfile.write_data.eq(i + 1)
                yield Tick()
                yield registerfile.write_enable.eq(0)
                yield Tick()
                yield Tick()
                print(f"Register {i} value: {(yield registerfile.read_data)}")
                assert (yield registerfile._out_of_bounds) == 0
                assert (yield registerfile.read_data) == i + 1

        @test
        def address_out_of_bounds():
            print("Some data")
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
            yield Tick()
            print(f"Register 0 value: {(yield registerfile.read_data)}")
            print(f"Actual address: {(yield registerfile.address)}")
            print(f"Address: {(yield registerfile._address)}")
            print(f"is_for_me: {(yield registerfile.is_for_me)}")
            assert (yield registerfile._out_of_bounds) == 1
            assert (yield registerfile.read_data) == 0x0

        @test
        def to_small_address():
            yield registerfile.address.eq(0x00)
            yield registerfile.write_enable.eq(1)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            yield Tick()
            yield registerfile.write_enable.eq(0)
            yield Tick()
            yield Tick()
            assert (yield registerfile.read_data) == 0x0

        @test
        def register_file():
            yield registerfile.write_enable.eq(1)
            yield registerfile.address.eq(0x00 + registerfile.start_address)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            print(f"Register 0 value: {(yield registerfile.read_data)}")
            yield registerfile.write_enable.eq(0)
            yield Tick()
            print(f"Register 0 value: {(yield registerfile.read_data)}")
            yield Settle()
            yield Tick()
            print(f"Register 0 value: {(yield registerfile.read_data)}")
            print((yield registerfile.is_for_me))
            print(f"Is for me: {(yield registerfile.is_for_me)}")
            print(f"Internal address: {(yield registerfile._address)}")
            print(f"Address: {(yield registerfile.address)}")
            # print(f"Is out of bounds: {(yield registerfile._out_of_bounds)}")
            print((yield registerfile._address))
            print((yield registerfile.address))
            assert (yield registerfile.read_data) == 0x0000111

        @test
        def write_to_2_read_from_3():
            yield registerfile.write_enable.eq(1)
            yield registerfile.address.eq(0x04 + registerfile.start_address)
            yield registerfile.write_data.eq(0x0000111)
            yield Tick()
            yield Tick()
            yield registerfile.write_enable.eq(0)
            print(f"Register 2 value: {(yield registerfile.read_data)}")
            yield registerfile.address.eq(0x08 + registerfile.start_address)
            yield Tick()
            yield Tick()
            print(f"Register 3 value: {(yield registerfile.read_data)}")
            assert (yield registerfile.read_data) == 0x0

    @simulation(registermap=registermap)
    def reg_map():
        @test
        def register_map():
            cycle_counter = 0
            working_register = registermap.BaseAddresses.CLICINTTRIG
            value_to_write = 0x0000111
            yield registermap.address.eq(working_register)
            yield registermap.write_enable.eq(1)
            yield registermap.write_data.eq(value_to_write)
            yield Tick()
            yield Tick()
            yield registermap.write_enable.eq(0)
            yield Tick()
            yield Tick()
            yield registermap.address.eq(working_register)
            yield Tick()
            yield Tick()
            yield Tick()
            yield Tick()
            yield Tick()
            yield Tick()
            print(f"Register 0 value: {(yield registermap.read_data)}")
            assert (yield registermap.read_data) == 0x0000111

        @test
        def write_all_read_all():
            for i, reg in enumerate(registermap.write_able_addresses):
                write_value = i + 1
                print(f"Register {reg.name} @0x{reg.value:x}")
                yield registermap.address.eq(reg.value.as_integer_ratio()[0])
                yield registermap.write_enable.eq(1)
                yield registermap.write_data.eq(write_value)
                yield Tick()
                yield registermap.write_enable.eq(0)
                yield Tick()
                yield registermap.address.eq(reg.value)
                yield Tick()
                yield Tick()
                print(f"Register {reg.name} value: {(yield registermap.read_data)}")

                # assert (yield registermap.read_data) == i

        @test
        def write_to_one_read_from_all():
            yield registermap.address.eq(
                registermap.BaseAddresses.CLICCFG.value.as_integer_ratio()[0]
            )
            yield registermap.write_enable.eq(1)
            yield registermap.write_data.eq(0x0000111)
            yield Tick()
            yield registermap.write_enable.eq(0)

            for reg in registermap.write_able_addresses:
                yield registermap.address.eq(reg)
                yield Tick()
                yield Tick()
                print(f"Register {reg.name} value: {(yield registermap.read_data)}")
                if reg == registermap.BaseAddresses.CLICCFG:
                    assert (yield registermap.read_data) == 0x0000111
                else:
                    print(f"Register {reg.name} value: {(yield registermap.read_data)}")

    def generate_tests(func):
        # This function generates all the tests for the register map
        # Test case 1 : Write to each register, read from each register assert that the value is the same
        # Test case 2 : Write to one register assert that all other registers are not affected
        pass

    reg_file()
    reg_map()
