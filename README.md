# OoO470

Before running the simulation, you need to input the name of the .json 
in the ```main``` (line 181) and give it as an argument to the function ```parse_instruction```, 
e.g if the .json is test.json: <br/>
```parse_instruction("test.json")```
<br/>

To run the simulation run in a terminal:<br/>
```python OoO470.py```

The results are available in ```sim_results.json```


## Data Structures
Apart from the pre-defined structures given in the assignment, this design
also uses three additional FIFOs: one for the forwarding paths, and the other
two for the outputs of the ALU1 and ALU2.
The state of the forwarding path is not propagated from one cycle to another
as its content (a tuple of (entry, exception, result) where entry corresponds to 
an entry in the Integer Queue) can be used immediately by the other stages.

## Exception Mode

### Forwarding path
When the commit stage sees an instructions that is not done yet, but whose
results are available from the forwarding path, it sets the instruction to done and write 
the results in the physical register file. If this instruction also triggers an exception, 
then it sets the exception flag for the instructions in the active list.

### Commit
When the commit stage encounters an instructions that is done but has been flagged as 
triggering an exception, it sets the exception flag and exception PC at the end of the cycle.
The PC is set to 0x10000 and the Decoded Instruction Register as well as the Integer Queue 
and the forwarding paths are emptied. These changes will be visible to the other 
stages in the next cycle.
In this next cycle, the processor sees the exception flag and enters the Exception Mode, 
where the commit stage starts to rollback.


