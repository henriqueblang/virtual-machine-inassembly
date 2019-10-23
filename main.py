from virtual_machine import clearInput, VM

if __name__ == "__main__":

    # Input for Inassembly source file

    srcFile = input("Source file: ")

    with open(srcFile) as file:

        print("Clearing input...")

        # Clear input (remove commentary and blank space)
        code = clearInput(file.read())

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

        file.close()