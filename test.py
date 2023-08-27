def test_register_map():
    from amaranth.sim import Simulator, Tick, Settle
    cycle_counter = 0
    working_register = registermap.BaseAddresses.CLICINTTRIG
    value_to_write = 0x0000111

    yield registermap.address.eq(working_register.value)
    yield Tick()
    cycle_counter += 1
    print(f"Writing to address: 0x{(yield registermap.address):x}")
    assert (
        yield registermap.address
    ) == working_register.value  # Ensure address is correct

    yield registermap.write_data.eq(value_to_write)
    yield registermap.write_enable.eq(1)

    yield Tick()
    cycle_counter += 1
    assert (
        yield registermap.write_data
    ) == value_to_write, f"@{cycle_counter} Write data should be 0x{value_to_write:x} but is 0x{(yield registermap.write_data):x} "
    assert (
        yield registermap.write_enable
    ) == 1, "Write enable should be high"  # Ensure write enable is high
    print("Writing data...")
    print(f"Register {working_register} value: {(yield registermap.read_data)}")
    yield Tick()
    print(f"Register {working_register} value: {(yield registermap.read_data)}")
    yield Settle()
    yield Tick()
    yield Tick()
    yield Tick()
    print(f"Register {working_register} value: {(yield registermap.read_data)}")
    yield Tick()
    assert (yield registermap.read_data) == 0x0000111
