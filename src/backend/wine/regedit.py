from typing import NewType

from bottles.utils import UtilsLogger # pyright: reportMissingImports=false
from bottles.backend.wine.wineprogram import WineProgram

logging = UtilsLogger()

# Define custom types for better understanding of the code
BottleConfig = NewType('BottleConfig', dict)


class Regedit(WineProgram):
    program = "WINE Registry Editor"
    command = "regedit"
