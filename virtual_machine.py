import re

MNEMONICS_TRANSLATION = {
    "add": 0,
    "addi": 1,
    "sub": 2,
    "subi": 3,
    "mult": 4,
    "multi": 5,
    "div": 6,
    "divi": 7,
    "load": 8,
    "store": 9,
    "jump": 10,
    "bgt": 11,
    "blt": 12,
    "beq": 13,
    "move": 14,
    "inout": 15                      
}

REGISTERS_TRANSLATION = {
    "r0": 0,
    "@0": 0,
    "r1": 1,
    "@1": 1,
    "r2": 2,
    "@2": 2,
    "r3": 3,
    "@3": 3,
    "r4": 4,
    "@4": 4,
    "r5": 5,
    "@5": 5,
    "zero": 6,
    "@6": 6,
    "r7": 7,
    "@7": 7
}

# Padding required to complete a 32-bit instruction
# Key is instruction op-code, value is amount of zeroes after op-code
INSTRUCTION_PADDING = {
    0: 19,
    2: 19,
    4: 19,
    6: 19,
    8: 3,
    9: 3,
    10: 6,
    14: 22,
    15: 25
}

def commentRemover(text):
    # https://stackoverflow.com/questions/241327/remove-c-and-c-comments-using-python

    def replacer(match):
        s = match.group(0)

        if s.startswith('/'):
            return " "
        else:
            return s

    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )

    return re.sub(pattern, replacer, text)

def clearInput(input):
    output = []
    output.extend((commentRemover(input).replace(",", " ")).split())

    return output

class VM:

    # Architecture of 32 bits
    ARCHITECTURE_SIZE = 32

    def __init__(self):

        # Memory initialization
        self.programMemory = []
        self.dataMemory = {}

        # Registers initialization
        self.registers = {
            0: 0,                    # r0
            1: 0,                    # r1
            2: 0,                    # r2
            3: 0,                    # r3
            4: 0,                    # r4
            5: 0,                    # r5
            6: 0,                    # zero
            7: 0                     # Program Counter
        }

    # Show Virtual Machine memory
    def show(self, printProgramMemory = False):
        if printProgramMemory:
            print("Program memory: ")

            for address, data in enumerate(self.programMemory):
                hexAddress = "0x%0.2X" % address

                print("[" + hexAddress + "] " + bin(data))    

            print()

        print("Data memory: ")

        for address, data in self.dataMemory.items():
            hexAddress = "0x%0.2X" % address

            print("[" + hexAddress + "] " + str(data))

        print("\nRegisters: ")

        for register, data in self.registers.items():
            registerName = register != 6 and "r" + str(register) or "zero"

            print(registerName + ": " + str(data))

        print()

    # Translate source code into machine code
    def translate(self, original):

        # Position which the next translated instruction will be stored in the program memory
        programMemoryPointer = 0

        # Translated instruction buffer
        instructionTranslated = 0

        # Bit shifting helper
        shiftHelper = self.ARCHITECTURE_SIZE

        # Regex to match label definition
        labelRegex = re.compile("^([a-zA-Z_]+[a-zA-Z_0-9]*):\r?\n?$")

        # Label mapping
        labelMapping = {}

        # Dictionary of instructions to be updated after a label is defined
        instructionUpdate = {}

        for data in original:

            if data in MNEMONICS_TRANSLATION:
                # Matched a mnemonic, translate to binary opcode and add to translated instruction buffer
                opcode = MNEMONICS_TRANSLATION[data]

                shiftHelper -= 4

                instructionTranslated |= (opcode << shiftHelper)

                # Padding in order to complete a 32-bit instruction
                if opcode in INSTRUCTION_PADDING:
                    shiftHelper -= INSTRUCTION_PADDING[opcode]

            elif data in REGISTERS_TRANSLATION:
                # Matched a register, translate to binary register identification and add to translated instruction buffer
                shiftHelper -= 3

                instructionTranslated |= (REGISTERS_TRANSLATION[data] << shiftHelper)
            else:
                # Handling data that is neither a mnemonic nor a register
                # That is, a possible immediate value to arithmetics purpose, address or label

                try:
                    # https://stackoverflow.com/questions/209513/convert-hex-string-to-int-in-python
                    immediateData = int(data, 0)
                    shiftHelper -= 22

                    instructionTranslated |= (immediateData << shiftHelper)
                except ValueError:
                    # Probably it's a label

                    if not labelRegex.match(data):
                        # It's either a label called in a jump or branch or a syntax error
                        # Let's assume it's a label

                        shiftHelper -= 22
                        if data in labelMapping:
                            # The supposed label is already mapped, let's write its address

                            instructionTranslated |= (labelMapping[data] << shiftHelper)
                        else:
                            # The supposed label is not mapped yet, let's store the instruction address in order to update it later
                            # While we can't update the instruction, it'll have a dummy address written instead of the label (maybe) 
                            # future address

                            # label -> [(data), (data)]
                            # 1 -> address (index in programMemory)
                            # 2 -> string index which the address starts

                            if data in instructionUpdate:
                                instructionUpdate[data].append([programMemoryPointer, shiftHelper])
                            else:
                                instructionUpdate[data] = [[programMemoryPointer, shiftHelper]]
                    else:
                        # It's a label definition
                        labelData = labelRegex.search(data)
                        label = labelData.group(1) 
                        
                        # Check if the label is already mapped
                        if label in labelMapping:
                            print("Error [label already defined]")

                            return False
                        
                        labelMapping[label] = programMemoryPointer

                        # Check if there are any instructions to update with the label address
                        if label in instructionUpdate:

                            # Iterare through instructions to update and replace dummy address with label address
                            for instructionData in instructionUpdate[label]:
                                programMemoryAddress = instructionData[0]
                                dummyAddressStart = instructionData[1]

                                self.programMemory[programMemoryAddress] |= (programMemoryPointer << dummyAddressStart)

                            del instructionUpdate[label]   

            # If the instruction size limit is reached, store in program memory and advance pointer to store the next instruction
            if shiftHelper <= 0:
                self.programMemory.append(instructionTranslated)

                shiftHelper = self.ARCHITECTURE_SIZE
                instructionTranslated = 0

                programMemoryPointer += 1

        # If there are any instructions remaining to update, there is probably a syntax error (or a label definition is missing)
        if instructionUpdate:
            print("Error [syntax or label definition missing]")

            return False

        return True

    # Process machine code
    def process(self):
        
        # Address of instruction to be processed (Program Counter value)
        instructionAddress = self.registers[7]

        # Update Program Counter
        self.registers[7] += 1

        if instructionAddress >= len(self.programMemory):
            print("Reached end of program memory, the application is finalized.")

            return False

        # Recovering instruction from program memory
        instruction = self.programMemory[instructionAddress]

        shiftHelper = self.ARCHITECTURE_SIZE

        # Recovering op-code from instruction (first 4 bits)
        shiftHelper -= 4

        opcode = (instruction >> shiftHelper) & 0x0F

        # Invalid op-code
        if not opcode in self.OPCODES_METHOD:
            print("Error when processing instruction " + bin(instruction) + " at address " + bin(instructionAddress) + ", invalid opcode (" + bin(opcode) + ")")

            return False 

        # Get class method corresponding to op-code in order to process the instruction
        processingMethod = self.OPCODES_METHOD[opcode]

        # Ignore padding when processing instruction inside method
        if opcode in INSTRUCTION_PADDING:
            shiftHelper -= INSTRUCTION_PADDING[opcode]

        return processingMethod(self, instruction, shiftHelper)

    # Add 2 registers
    def add(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0000 0 (19) rdest (3) rsrc1 (3) rsrc2 (3)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister2 = (instruction >> shiftHelper) & 0x07

        # destinationRegister = sourceRegister1 + sourceRegister2
        self.registers[destinationRegister] = self.registers[sourceRegister1] + self.registers[sourceRegister2]

        return True

    # Add 1 register and 1 immediate
    def addi(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0001 rdest (3) rsrc1 (3) imm (22)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        immediate = (instruction >> shiftHelper) & 0x3FFFFF

        # destinationRegister = sourceRegister1 + immediate
        self.registers[destinationRegister] = self.registers[sourceRegister1] + immediate

        return True

    # Subtract 2 registers
    def sub(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0010 0 (19) rdest (3) rsrc1 (3) rsrc2 (3)

        shiftHelper -= 3
        destinationRegister = instruction & (1 << shiftHelper)

        shiftHelper -= 3
        sourceRegister1 = instruction & (1 << shiftHelper)

        shiftHelper -= 3
        sourceRegister2 = instruction & (1 << shiftHelper)

        # destinationRegister = sourceRegister1 - sourceRegister2
        self.registers[destinationRegister] = self.registers[sourceRegister1] - self.registers[sourceRegister2]

        return True

    # Subtract 1 register and 1 immediate
    def subi(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0011 rdest (3) rsrc1 (3) imm (22)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        immediate = (instruction >> shiftHelper) & 0x3FFFFF

        # destinationRegister = sourceRegister1 - immediate
        self.registers[destinationRegister] = self.registers[sourceRegister1] - immediate

        return True

    # Multiply 2 registers
    def mult(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0100 0 (19) rdest (3) rsrc1 (3) rsrc2 (3)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister2 = (instruction >> shiftHelper) & 0x07

        # destinationRegister = sourceRegister1 * sourceRegister2
        self.registers[destinationRegister] = self.registers[sourceRegister1] * self.registers[sourceRegister2]

        return True

    # Multiply 1 register and 1 immediate
    def multi(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0101 rdest (3) rsrc1 (3) imm (22)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        immediate = (instruction >> shiftHelper) & 0x3FFFFF

        # destinationRegister = sourceRegister1 * immediate
        self.registers[destinationRegister] = self.registers[sourceRegister1] * immediate

        return True

    # Divide 2 registers
    def div(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0111 0 (19) rdest (3) rsrc1 (3) rsrc2 (3)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister2 = (instruction >> shiftHelper) & 0x07

        # destinationRegister = sourceRegister1 / sourceRegister2
        self.registers[destinationRegister] = int(self.registers[sourceRegister1] / self.registers[sourceRegister2])

        return True

    # Divide 1 register and 1 immediate
    def divi(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 0111 rdest (3) rsrc1 (3) imm (22)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        immediate = (instruction >> shiftHelper) & 0x3FFFFF

        # destinationRegister = sourceRegister1 / immediate
        self.registers[destinationRegister] = int(self.registers[sourceRegister1] / immediate)

        return True
        
    # Load data from data memory
    def load(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1000 0 (3) rdest (3) address (22)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        address = (instruction >> shiftHelper) & 0x3FFFFF

        # Default value for addresses that were not updated by a store instruction
        if not address in self.dataMemory:
            self.dataMemory[address] = 0

        # destinationRegister = value at address (data memory)
        self.registers[destinationRegister] = self.dataMemory[address]

        return True

    # Store data in data memory
    def store(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1001 0 (3) rsrc (3) address (22)  

        shiftHelper -= 3
        sourceRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        address = (instruction >> shiftHelper) & 0x3FFFFF

        # value at address (data memory) = sourceRegister
        self.dataMemory[address] = self.registers[sourceRegister]

        return True

    # Jump to address
    def jump(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1010 0 (6) address (22)  

        shiftHelper -= 22
        address = (instruction >> shiftHelper) & 0x3FFFFF

        # Jump (change address of Program Counter) to address
        self.registers[7] = address

        return True

    # Jump to branch if register_1 > register_2
    def bgt(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1011 rsrc1 (3) rsrc2 (3) address (22)

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister2 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        address = (instruction >> shiftHelper) & 0x3FFFFF

        # Jump (change address of Program Counter) to address if sourceRegister1 > sourceRegister2
        if self.registers[sourceRegister1] > self.registers[sourceRegister2]:
            self.registers[7] = address

        return True

    # Jump to branch if register_1 < register_2
    def blt(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1100 rsrc1 (3) rsrc2 (3) address (22)

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister2 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        address = (instruction >> shiftHelper) & 0x3FFFFF

        # Jump (change address of Program Counter) to address if sourceRegister1 < sourceRegister2
        if self.registers[sourceRegister1] < self.registers[sourceRegister2]:
            self.registers[7] = address

        return True

    # Jump to branch if register_1 == register_2
    def beq(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1101 rsrc1 (3) rsrc2 (3) address (22)

        shiftHelper -= 3
        sourceRegister1 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister2 = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 22
        address = (instruction >> shiftHelper) & 0x3FFFFF

        # Jump (change address of Program Counter) to address if sourceRegister1 = sourceRegister2
        if self.registers[sourceRegister1] == self.registers[sourceRegister2]:
            self.registers[7] = address

        return True

    # Set value of destination register to value of source register
    def move(self, instruction, shiftHelper):

        # Recover relevant data to process from instruction
        # 1110 0 (22) rdest (3) rsrc (3)

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        shiftHelper -= 3
        sourceRegister = (instruction >> shiftHelper) & 0x07

        # destinationRegister = sourceRegister
        self.registers[destinationRegister] = self.registers[sourceRegister]

        return True

    # Input and output system call
    def inout(self, instruction, shiftHelper):
        
        # Recover relevant data to process from instruction
        # 1111 0 (25) rdest (3) 

        systemCall = self.registers[5]

        shiftHelper -= 3
        destinationRegister = (instruction >> shiftHelper) & 0x07

        # if r5 is 0 -> input
        # if r5 is 1 -> output
        # else error
        if systemCall == 0:    
            try:
                self.registers[destinationRegister] = int(input())
            except ValueError:

                # Input is not a integer and we are not handling strings
                print("Error when processing instruction " + bin(instruction) + ", inout (invalid input)")

                return False

        elif systemCall == 1:
            print(self.registers[destinationRegister])

        else:

            # Invalid system call
            print("Error when processing instruction " + bin(instruction) + ", inout (invalid system call)")

            return False

        return True

    OPCODES_METHOD = {
        0: add,
        1: addi,
        2: sub,
        3: subi,
        4: mult,
        5: multi,
        6: div,
        7: divi,
        8: load,
        9: store,
        10: jump,
        11: bgt,
        12: blt,
        13: beq,
        14: move,
        15: inout
    }