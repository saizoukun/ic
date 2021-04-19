import logging
import os
import time
import pathlib
import platform
from sudachipy import tokenizer
from sudachipy import dictionary

logger = logging.getLogger(__name__)

class SudachiAPI(object):
    def __init__(self, mode=1):
        self.tokenizer_obj = dictionary.Dictionary().create()
        if mode == 2:
            self.mode = tokenizer.Tokenizer.SplitMode.B
        elif mode == 3:
            self.mode = tokenizer.Tokenizer.SplitMode.A
        else:
            self.mode = tokenizer.Tokenizer.SplitMode.B


    def getTokenizeSplit(self, keyword, cascede=""):
        if cascede == "":
            result = [m.surface() for m in self.tokenizer_obj.tokenize(keyword, self.mode)]
        else:
            result = [m.surface() for m in self.tokenizer_obj.tokenize(keyword, self.mode) if m.part_of_speech()[0] == cascede]
        return result

