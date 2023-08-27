def register_map():
    from amaranth.sim import Tick, Settle, Simulator
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

def write_all_read_all():
    from amaranth.sim import Tick, Settle, Simulator
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

def write_to_one_read_from_all():
    from amaranth.sim import Tick, Settle, Simulator
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
