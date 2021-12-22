import colorama

def bold(str)->str:
    return colorama.Style.BRIGHT + str + colorama.Style.RESET_ALL
