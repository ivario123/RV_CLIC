from typing import Callable, List
from amaranth.sim import Simulator
from amaranth import Elaboratable


def run(base_module, process: List[Callable], file_names: List[str] = None):
    if file_names and len(process) != len(file_names):
        raise ValueError("process and file_names must have the same length")
    for i in range(len(process)):
        print(f"Running simulation for {process[i].__name__}")
        _run(base_module, process[i], file_names[i] if file_names else None)


import os
from difflib import SequenceMatcher


def _run(base_module: Elaboratable, process: Callable, file_name: str = None):
    # Check if the environment variable $EMIT is set to 1 (or ALL) or similar to function name
    emit = os.environ.get("EMIT", "0")
    emit_this = ["ALL", "1", process.__name__]
    if emit in emit_this or SequenceMatcher(None, emit, process.__name__).ratio() > 0.9:
        print("Emitting vcd for " + process.__name__)
        emit = True
    else:
        emit = False

    sim = Simulator(base_module)
    sim.add_process(process)
    sim.add_clock(1e-6)
    file_name = file_name or base_module.__class__.__name__ + "@" + process.__name__
    print(f"Running simulation for {file_name}")

    def sim_run(*_, **__):
        try:
            sim.run()
            print(f"Simulation passed for {file_name}")
        except Exception as e:
            print(
                f"ERROR : Simulation failed for {file_name} with error {e}",
            )
            raise e

    if emit:
        with sim.write_vcd(
            "./sims/" + file_name + ".vcd",
            "./sims/" + file_name + ".gtkw",
        ):
            sim_run()
    else:
        sim_run()

    return sim
