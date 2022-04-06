class Entry:
    def __init__(self, dest_register, op_a_is_ready, op_a_reg_tag, op_a_value, op_b_is_ready, op_b_reg_tag,
                 op_b_value, op_code, pc):

        self.dest_register = dest_register  # destination physical register
        self.op_a_is_ready = op_a_is_ready
        self.op_a_reg_tag = op_a_reg_tag
        self.op_a_value = op_a_value
        self.op_b_is_ready = op_b_is_ready
        self.op_b_reg_tag = op_b_reg_tag
        self.op_b_value = op_b_value
        self.op_code = op_code
        self.pc = pc

    def to_dict(self):
        return {
            "DestRegister": self.dest_register,
            "OpAIsReady": self.op_a_is_ready,
            "OpARegTag": self.op_a_reg_tag,
            "OpAValue": self.op_a_value,
            "OpBIsReady": self.op_b_is_ready,
            "OpBRegTag": self.op_b_reg_tag,
            "OpBValue": self.op_b_value,
            "OpCode": self.op_code,
            "PC": self.pc
        }
