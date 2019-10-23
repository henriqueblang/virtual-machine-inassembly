from virtual_machine import clearInput, VM

with open("test.inasm") as f:

    print("Clearing input...")

    # Clear input (remove commentary and blank space)
    code = clearInput(f.read())

    print("Done clearing.")

    # Instantiate the virtual machine
    myVM = VM()

    print("Translating Inassembly to machine code...")

    # Translate Inassembly code into machine code
    if myVM.translate(code):
        print("Done translating.")

        print(myVM.programMemory)

        option = input("Process step by step [y/n]? ")

        # Process instructions
        while myVM.process():
            print(myVM.registers)
            print(myVM.dataMemory)

            if option == 'y':
                input("Press enter to continue...")

    f.close()