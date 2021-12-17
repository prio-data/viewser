from functools import partial
import itertools

print_no_newline = partial(print, end = "", flush = True)

class WaitingAnimation():
    CYCLE = ["-","\\", "|", "/"]
    def __init__(self, message: str = ""):
        self._animation_cycle = itertools.cycle(self.CYCLE)
        self._previous_output = ""
        self._message = message

    def _erase_prev(self):
        print_no_newline("\b" * len(self._previous_output))

    def print_next(self):
        to_print = self._message + " " + next(self._animation_cycle)
        self._erase_prev()
        self._previous_output = to_print
        print_no_newline(to_print)

    def end(self):
        self._erase_prev()

class LineAnimation(WaitingAnimation):
    CYCLE = [
        ".     ",
        " o    ",
        "  O   ",
        "   O  ",
        "    o ",
        "     .",
        ]
