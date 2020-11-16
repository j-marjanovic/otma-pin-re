
## Procedure

1. start with a base project and a list of pin locations to test
2. compile the project for the first time
3. for each pin location in the list of pin locations ...
    1. ECO the pin to the pin location from the list
    2. for drive strength in {4mA, 8mA, 12mA} ...
        1. ECO the driving strength
        2. prepare the .cof file (output filename)
        3. generate .jic file
