def isAllDigits(src: str, length: int = -1) -> bool:
    for i in src:
        if i < '0' or i > '9':
            return False
    return length == -1 or len(src) == length