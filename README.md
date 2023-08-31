# RV_CLIC

Vhdl implementation of Core-Local Interrupt Controller (CLIC).

## Simulation

```bash
export SIMULATE=1 # Or export SIMULATE=<simulation name>
export EMIT=ALL # Or export EMIT=<test name> # Note that test name is not the same as simulation name
export POOL_SIZE=3 # Or export POOL_SIZE=<number of threads>
python clic --sim
```
