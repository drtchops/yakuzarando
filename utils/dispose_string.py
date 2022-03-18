# -*- coding: utf-8 -*-
# Taken from https://gist.github.com/CapitanRetraso/56a00a70083457c257dad029622eae9f
import binascii
import functools
import json
import struct
import sys
from collections import OrderedDict
from typing import List

file_path = ""
file_name = ""
hexFile = b""
rebuildFileTemp = b""
exportDict = OrderedDict()
stringOffsetTable: List[str] = []
stringTable = []


def readFromPosition(offset, size, value_type):
    valueToRead = binascii.unhexlify(hexFile[offset * 2 : (offset + size) * 2])
    valueToRead = struct.unpack(value_type, valueToRead)
    valueToRead = functools.reduce(lambda rst, d: rst * 10 + d, (valueToRead))
    # String gets unpacked as bytes, we want to convert it to a regular string
    if type(valueToRead) is bytes:
        valueToRead = valueToRead.decode()
    return valueToRead


# Calculates the amount of null bytes that need to be added
def calculateSeparator(end):
    last_part_offset = int(hex(int(end))[-1], 16)

    # Check the last digit of the hex value to calculate the amount that needs to be filled for the next table to start
    if last_part_offset < 0x4:
        return 0x4 - last_part_offset
    elif last_part_offset >= 0x4 and last_part_offset < 0x8:
        return 0x8 - last_part_offset
    elif last_part_offset >= 0x8 and last_part_offset < 0xC:
        return 0xC - last_part_offset
    elif last_part_offset >= 0xC and last_part_offset < 0x10:
        return 0x10 - last_part_offset
    else:
        return 1


# Stores every entry of the table into the selected variable
def storeTable(startOffset, tableSize, tableContainer):
    byteGroup = ""
    table = hexFile[(startOffset * 2) : (startOffset * 2) + (tableSize * 4) * 2].decode(
        "shift-jis"
    )

    for nibble in table:
        if len(byteGroup) < 8:
            byteGroup += nibble

        if len(byteGroup) == 8:
            tableContainer.append(byteGroup)
            byteGroup = ""


def iterateStringTable():
    for offset in stringOffsetTable:
        # A bit of a dirty approach but it will do for now
        table = hexFile[(int(offset, 16) * 2) :]
        string_end = table.find(b"00")
        if (
            string_end % 2 != 0
        ):  # If the last hex digit ends with 0, the pointer will be odd, so we compensate adding 1
            string_end += 1
        string = binascii.unhexlify(table[:string_end]).decode("shift-jis")
        stringTable.append(string)


def exportFile():
    with open(file_path, "rb") as f:
        file = f.read()
    global hexFile
    hexFile = binascii.hexlify(file)

    numberOfElements = readFromPosition(0x0, 0x2, ">H")
    pointerToStringOffsetTable = readFromPosition(0x4, 0x4, ">I")

    # DEBUG
    print("Number of Elements: " + str(numberOfElements))
    print("Pointer to String Offset Table: " + str(pointerToStringOffsetTable))
    storeTable(pointerToStringOffsetTable, numberOfElements, stringOffsetTable)
    iterateStringTable()

    exportDict["NUMBER_ELEMENTS"] = numberOfElements
    for element in stringTable:
        element_index = stringTable.index(element)
        exportDict[element_index] = element

    with open(file_name + ".json", "w") as file:
        json.dump(exportDict, file, indent=2)


def rebuildFile():
    data: dict
    with open(file_path, "r") as file:
        data = json.load(file)

    global rebuildFileTemp
    stringOffsetTableTemp = []
    rebuildFileTemp += binascii.hexlify(data["NUMBER_ELEMENTS"].to_bytes(2, "big"))
    rebuildFileTemp += b"0000"
    rebuildFileTemp += b"00000000"  # Temp offset table pointer

    # Write String table and store offsets for the String offset table
    for x in range(data["NUMBER_ELEMENTS"]):
        stringOffsetTableTemp.append(len(rebuildFileTemp) / 2)
        rebuildFileTemp += binascii.hexlify(data.get(str(x), "").encode("shift-jis"))
        rebuildFileTemp += b"00"  # Null byte
    # Add null bytes at the end of the String table
    rebuildFileTemp += b"00" * calculateSeparator(len(rebuildFileTemp) / 2)

    stringOffsetTableOffset = len(rebuildFileTemp) / 2
    for x in range(data["NUMBER_ELEMENTS"]):  # Write String Offset table
        rebuildFileTemp += hex(int(stringOffsetTableTemp[x]))[2:].zfill(8).encode()

    rebuildFileTemp = (
        rebuildFileTemp[: 0x4 * 2]
        + hex(int(stringOffsetTableOffset))[2:].zfill(8).encode()
        + rebuildFileTemp[0x8 * 2 :]
    )  # Add the pointer to the String Offset table to the main table

    with open(file_name + ".bin", "wb") as file:
        file.write(binascii.unhexlify(rebuildFileTemp))


# Switch case based on the file extension
def determineFileExtension(file_extension: str):
    switch = {
        "bin": exportFile,
        "json": rebuildFile,
    }
    func = switch.get(file_extension.lower(), lambda: "Extension not supported")
    return func()


def forFile(path: str):
    global file_path
    global file_name
    file_path = path
    file_name = file_path.split("\\")[-1]
    file_extension = file_name.split(".")[-1]
    determineFileExtension(file_extension)


if __name__ == "__main__":
    forFile(sys.argv[1:][0])
