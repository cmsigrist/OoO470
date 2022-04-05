import copy
import json

from Stages import fetch_and_decode, rename_and_dispatch, issue_stage, ALU1, ALU2, commit
from data_structures.ActiveList import EntryRecord
from data_structures.IQ import Entry

ACTIVE_LIST_LENGTH = 32
IQ_LENGTH = 32
PHYSICAL_REGISTER_FILE_LENGTH = 64
BUSY_BIT_TABLE_LENGTH = 64
DIR_LENGTH = 4
MAX_COMMIT = 4

logs = []

active_list = [] * ACTIVE_LIST_LENGTH
busy_bit_table = [False for i in range(BUSY_BIT_TABLE_LENGTH)]
DIR = [] * DIR_LENGTH
exception_flag = False
exception_PC = 0
free_list = [i for i in range(32, BUSY_BIT_TABLE_LENGTH)]
IQ = [] * IQ_LENGTH
PC = 0
physical_rf = [0] * PHYSICAL_REGISTER_FILE_LENGTH
register_map_table = [i for i in range(32)]
to_alu_1 = []
to_alu_2 = []

# next
active_list_next = [] * ACTIVE_LIST_LENGTH
busy_bit_table_next = [False for i in range(BUSY_BIT_TABLE_LENGTH)]
DIR_next = [] * DIR_LENGTH
exception_flag_next = False
exception_PC_next = 0
free_list_next = [i for i in range(32, BUSY_BIT_TABLE_LENGTH)]
IQ_next = [] * IQ_LENGTH
PC_next = 0
physical_rf_next = [0] * PHYSICAL_REGISTER_FILE_LENGTH
register_map_table_next = [i for i in range(32)]


def parse_instruction(filename):
    # Opening JSON file
    f = open(filename)
    # returns JSON object as a dictionary
    instructions = json.load(f)
    # Closing file
    f.close()
    return instructions


def no_instruction(instructions):
    return PC >= len(instructions) and len(DIR) == 0 and \
        len(active_list) == 0 and len(IQ) == 0


def propagate(instructions):
    global active_list_next
    global busy_bit_table_next
    global DIR_next
    global exception_flag_next
    global exception_PC_next
    global free_list_next
    global IQ_next
    global PC_next
    global physical_rf_next
    global register_map_table_next
    global to_alu_1
    global to_alu_2

    # make copy of all data structures
    active_list_next = list(active_list)
    busy_bit_table_next = list(busy_bit_table)
    DIR_next = list(DIR)
    exception_flag_next = exception_flag
    exception_PC_next = exception_PC
    free_list_next = list(free_list)
    IQ_next = list(IQ)
    PC_next = PC
    physical_rf_next = list(physical_rf)
    register_map_table_next = list(register_map_table)

    forwarding_path = []  # [(entry, exception, result)]

    # update the value of these copies according to the functionality of all
    # units -> combinational logic
    forwarding_path = ALU2(
        to_alu_2,
        exception_flag,
        forwarding_path
    )

    active_list_next, IQ_next, busy_bit_table_next, free_list_next,\
        register_map_table_next, physical_rf_next, forwarding_path, \
        exception_PC_next, exception_flag_next = commit(
            active_list,
            busy_bit_table,
            free_list,
            register_map_table,
            physical_rf,
            forwarding_path,
            IQ_next,
            exception_PC,
            exception_flag
        )
    to_alu_2 = ALU1(to_alu_1, exception_flag)

    to_alu_1, IQ_next = issue_stage(IQ, exception_flag, forwarding_path)

    DIR_next, free_list_next, busy_bit_table_next, register_map_table_next,\
        physical_rf_next, active_list_next, IQ_next = rename_and_dispatch(
            DIR,
            instructions,
            free_list_next,
            busy_bit_table_next,
            register_map_table,
            physical_rf_next,
            active_list_next,
            IQ_next,
            exception_flag,
            forwarding_path
        )
    PC_next, DIR_next = fetch_and_decode(
        PC, DIR_next, instructions, exception_flag)

    # All units will read the current state of the processor except those that
    # access data structures that can be updated and read in the same cycle
    # (e.g., queues)
    return 0


def latch():
    global active_list
    global busy_bit_table
    global DIR
    global exception_flag
    global exception_PC
    global free_list
    global IQ
    global PC
    global physical_rf
    global register_map_table

    active_list = active_list_next
    busy_bit_table = busy_bit_table_next
    DIR = DIR_next
    exception_flag = exception_flag_next
    exception_PC = exception_PC_next
    free_list = free_list_next
    IQ = IQ_next
    PC = PC_next
    physical_rf = physical_rf_next
    register_map_table = register_map_table_next


def dump_state_into_log():
    state = {
        "ActiveList": [EntryRecord.to_dict(entry_rec) for entry_rec in active_list],
        "BusyBitTable": busy_bit_table,
        "DecodedPCs": DIR,
        "Exception": exception_flag,
        "ExceptionPC": exception_PC,
        "FreeList": free_list,
        "IntegerQueue": [Entry.to_dict(entry) for entry in IQ],
        "PC": PC,
        "PhysicalRegisterFile": physical_rf,
        "RegisterMapTable": register_map_table
    }

    new_state = copy.deepcopy(state)
    logs.append(new_state)


def save_log():
    # Directly from dictionary
    with open('logs.json', 'a') as outfile:
        json.dump(logs, outfile)


def main():
    # parse JSON to get the program
    instructions = parse_instruction("test_exception.json")
    # dump the state of the reset system
    dump_state_into_log()
    # the loop for cycle-by-cycle iterations.
    i = 0
    while not (no_instruction(instructions)):
        # do propagation
        propagate(instructions)
        # advance clock, start next cycle
        latch()
        # dump the state
        dump_state_into_log()
        i += 1

    # save the output JSON log
    save_log()

    return


if __name__ == "__main__":
    main()
