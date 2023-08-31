from typing import Callable, List
from amaranth.sim import Simulator
from amaranth import Elaboratable
import os
from difflib import SequenceMatcher
from threading import Thread, Lock

mutex = Lock()
threadpool = []
max_pool_size = os.environ.get("POOL_SIZE", 3)


def pool_manager():
    from time import sleep

    while 1:
        with mutex:
            for t in threadpool:
                t.handled = not t.is_alive()
            threadpool = [t for t in threadpool if t.handled]
        sleep(2)
        if len(threadpool) == 0:
            print("All sims completed")
            return


def run(base_module, process: List[Callable], file_names: List[str] = []):
    if file_names and len(process) != len(file_names):
        raise ValueError("process and file_names must have the same length")
    manager = Thread(target=pool_manager)
    manager.start()
    for i in range(len(process)):
        print(f"Running simulation for {process[i].__name__}")
        thread = Thread(
            target=_run,
            args=(base_module, process[i], file_names[i] if file_names else None),
        )
        # _run(base_module, process[i], file_names[i] if file_names else None)
        thread.start()
        with mutex:
            threadpool.append(thread)
    manager.join()


def _run(base_module: Elaboratable, process: Callable, file_name: str = ""):
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
            print(e)
            raise e

    if emit:
        print(file_name)
        with sim.write_vcd(
            f"./sims/{file_name}.vcd",
            f"./sims/{file_name}.gtkw",
        ):
            sim.run()
    else:
        sim_run()

    return sim
