def isAllDigits(src: str, length: int = -1) -> bool:
    for i in src:
        if i < '0' or i > '9':
            return False
    return length == -1 or len(src) == length


def idx2stage(x: int) -> str:
    di = {
        0: 'Build', 1: 'Semantic', 5: 'Codegen', 6: 'Optimize', 7: 'End'
    }
    return di[x]


def idx2class(x: int) -> str:
    di = {
        0: 'table-danger', 1: 'table-info', 5: 'table-primary', 6: 'table-warning', 7: 'table-success'
    }
    return di[x]
