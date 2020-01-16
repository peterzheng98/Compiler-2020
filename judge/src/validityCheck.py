def checkValidWorkList(workList: list):
    for work in workList:
        if not 'uuid' in work.items():
            return False
        if not 'repo' in work.items():
            return False
        if not 'testCase' in work.items():
            return False
        if not 'stage' in work.items():
            return False
        if not 'subWorkId' in work.items():
            return False
    return True


def checkSemanticValidity(subDict: dict):
    if not 'inputSourceCode' in subDict.items():
        return False
    if not 'assertion' in subDict.items():
        return False
    if not 'timeLimit' in subDict.items():
        return False
    if not 'memoryLimit' in subDict.items():
        return False
    return True


def checkCodegenValidity(subDict: dict):
    if not 'inputSourceCode' in subDict.items():
        return False
    if not 'inputContent' in subDict.items():
        return False
    if not 'outputCode' in subDict.items():
        return False
    if not 'outputContent' in subDict.items():
        return False
    if not 'timeLimit' in subDict.items():
        return False
    if not 'memoryLimit' in subDict.items():
        return False
    return True
