from data_structures.ActiveList import EntryRecord
from data_structures.IQ import Entry

ACTIVE_LIST_LENGTH = 32
IQ_LENGTH = 32
PHYSICAL_REGISTER_FILE_LENGTH = 64
DIR_LENGTH = 4
MAX_COMMIT = 4


def fetch_and_decode(PC, DIR, instructions, exception_flag):
    # if Commit set the exception flag then change PC
    if exception_flag:
        # ask about this value
        PC = 0x10000
        DIR = []
    else:
        # can fetch up to 4 instructions and only if there are still instructions
        while len(DIR) < MAX_COMMIT and PC < len(instructions):
            # check if enough space in physical registers, in the Active List,
            # and in the IQ.
            DIR.append(PC)  # Fetch new instructions
            PC += 1
    return PC, DIR


def rename_and_dispatch(
        DIR,
        instructions,
        free_list,
        busy_bit_table,
        register_map_table,
        physical_rf,
        active_list,
        IQ,
        exception_flag,
        forwarding_path
):
    if not exception_flag:
        i = 0
        while i < MAX_COMMIT and len(DIR) > 0:
            # check if enough space in physical registers, in the Active List,
            # and in the IQ.
            if len(active_list) < ACTIVE_LIST_LENGTH and len(IQ) < IQ_LENGTH and \
                    (False in busy_bit_table):
                # rename the instructions decoded from the previous stage and
                # updated the Register Map Table and Free List accordingly.
                PC = DIR.pop(0)
                # "addi x1, x0, 1"
                next_instruction = instructions[PC].split(",")
                opcode_dest = next_instruction[0].split(" ")
                op_code = opcode_dest[0]

                dest = opcode_dest[1][opcode_dest[1].find('x') + 1:]
                logical_dest = int(dest)  # xi

                # init opA
                op_a = next_instruction[1][next_instruction[1].find(
                    'x') + 1:]  # look into mapping then prf
                # check map
                op_a_reg_tag = register_map_table[int(op_a)]
                op_a_is_ready = False
                op_a_value = 0
                # init opB
                op_b = next_instruction[2][next_instruction[2].find(
                    'x') + 1:]
                op_b_reg_tag = 0  # if opB is an imm, no need to have the value
                op_b_is_ready = False
                op_b_value = 0

                # check in busy_bit if opA is ready or not
                if busy_bit_table[op_a_reg_tag]:
                    for fp in forwarding_path:
                        if fp[0].dest_register == op_a_reg_tag:
                            op_a_is_ready = True
                            op_a_value = fp[2]
                else:
                    op_a_value = physical_rf[int(op_a_reg_tag)]
                    op_a_is_ready = True

                if op_code != "addi":
                    # check map
                    op_b_reg_tag = register_map_table[int(op_b)]
                    # check in busy_bit if opB is ready or not
                    if busy_bit_table[op_b_reg_tag]:
                        for fp in forwarding_path:
                            if fp[0].dest_register == op_b_reg_tag:
                                op_b_is_ready = True
                                op_b_value = fp[2]
                    else:
                        op_b_value = physical_rf[int(op_a_reg_tag)]
                        op_b_is_ready = True

                if op_code == "addi":
                    op_code = "add"
                    op_b_value = int(op_b)
                    op_b_is_ready = True

                # pop next free
                dest_register = free_list.pop(0)  # (32, 63)
                # set as busy
                busy_bit_table[int(dest_register)] = True
                # put the old dest
                old_dest = register_map_table[int(dest)]  # (0, 31)
                # update table with new mapping
                register_map_table[int(dest)] = dest_register  # (0, 31)

                # add new Entry to IQ
                IQ.append(Entry(
                    dest_register,
                    op_a_is_ready,
                    op_a_reg_tag,
                    op_a_value,
                    op_b_is_ready,
                    op_b_reg_tag,
                    op_b_value,
                    op_code,
                    PC))
                # add next EntryRecord to active list
                active_list.append(EntryRecord(logical_dest, old_dest, PC))
                i += 1
            else:  # no free space in the queues
                i = MAX_COMMIT
    return DIR, free_list, busy_bit_table, register_map_table, physical_rf, active_list, IQ


def issue_stage(IQ, exception_flag, forwarding_path):
    to_alu_1 = []
    if not exception_flag:
        i = 0
        j = 0
        while i < MAX_COMMIT and len(IQ) != 0 and j < len(IQ):
            next_entry = IQ[j]

            for fp in forwarding_path:
                if fp[0].dest_register == next_entry.op_a_reg_tag:
                    IQ[j].op_a_is_ready = True
                    IQ[j].op_a_value = fp[2]
                if fp[0].dest_register == next_entry.op_b_reg_tag:
                    IQ[j].op_b_is_ready = True
                    IQ[j].op_b_value = fp[2]

                # instruction is ready remove from IQ
            if next_entry.op_a_is_ready and next_entry.op_b_is_ready:
                to_alu_1.append(next_entry)
                IQ.pop(j)  # next_entry will still be at index j after pop
                i += 1
            else:
                j += 1

    return to_alu_1, IQ


def ALU1(to_alu_1, exception_flag):
    if not exception_flag:
        return list(to_alu_1)


def ALU2(to_alu_2, exception_flag, forwarding_path):
    if not exception_flag:
        for entry in to_alu_2:
            opcode = entry.op_code
            opA = int(entry.op_a_value)
            opB = int(entry.op_b_value)

            if opcode == "add":
                result = opA + opB
                forwarding_path.append((entry, False, result))
            elif opcode == "sub":
                result = opA - opB
                forwarding_path.append((entry, False, result))
            elif opcode == "mulu":
                result = opA * opB
                forwarding_path.append((entry, False, result))
            else:
                if opB == 0:
                    forwarding_path.append((entry, True, None))
                else:
                    if opcode == "divu":
                        result = opA / opB
                        forwarding_path.append((entry, False, result))
                    else:
                        result = opA % opB
                        forwarding_path.append((entry, False, result))

    # commit is supposed to update active_list
    return forwarding_path


def commit(
    active_list,
    busy_bit_table,
    free_list,
    register_map_table,
    physical_rf,
    forwarding_path,
    IQ,
    exception_PC,
    exception_flag
):
    i = 0
    is_done = True
    if not exception_flag:
        # commit up to 4 done instructions
        while i < MAX_COMMIT and is_done and len(active_list) != 0:
            next_op = active_list[0]
            if next_op.done:
                # goto exception
                if next_op.exception:
                    exception_flag = True
                    exception_PC = next_op.pc
                    is_done = False
                else:
                    # add oldDest to free list in cycle after busy is off
                    free_list.append(active_list[0].old_dest)
                    active_list.pop(0)
                    i += 1
            else:
                is_done = False

        j = 0
        # write value from forwarding path
        while len(forwarding_path) != 0 and j < len(active_list):
            next_op = active_list[j]
            next_fp_index = -1
            for k in range(len(forwarding_path)):
                if forwarding_path[k][0].pc == next_op.pc:
                    next_fp_index = k
            # the result of next op is available
            if next_fp_index >= 0:
                fp = forwarding_path[next_fp_index]
                active_list[j].done = True
                if fp[1]:  # Exception is True
                    active_list[j].exception = True
                else:
                    physical_rf[fp[0].dest_register] = fp[2]
                    busy_bit_table[fp[0].dest_register] = False
            j += 1
    else:  # Exception Mode
        # reset IQ and Execution stage
        forwarding_path = []
        IQ = [] * IQ_LENGTH
        active_list,
        register_map_table,
        free_list,
        # rollback
        busy_bit_table = rollback(
            active_list,
            register_map_table,
            free_list,
            busy_bit_table
        )

        if len(active_list) == 0:
            exception_flag = False
            exception_PC = 0

    return active_list, IQ, busy_bit_table, free_list, register_map_table, \
        physical_rf, forwarding_path, exception_PC, exception_flag


def rollback(active_list, register_map_table, free_list, busy_bit_table):
    i = 0

    while i < MAX_COMMIT and len(active_list) != 0:
        entry_record = active_list.pop()
        logical_dest = entry_record.logical_dest  # xi in (0, 31)
        # current maps xi in (0, 31) -> (0, 63)
        mapping = register_map_table[logical_dest]
        free_list.append(mapping)  # append back in free_list
        busy_bit_table[mapping] = False
        # restore mapping
        register_map_table[logical_dest] = entry_record.old_dest

        i += 1

    return active_list, register_map_table, free_list, busy_bit_table
