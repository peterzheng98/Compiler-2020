def checkValidWorkList(workList: list):
    for work in workList:
        if not 'uuid' in work.keys():
            return False
        if not 'repo' in work.keys():
            return False
        if not 'testCase' in work.keys():
            return False
        if not 'stage' in work.keys():
            return False
        if not 'subWorkId' in work.keys():
            return False
    return True


def checkSemanticValidity(subDict: dict):
    if not 'inputSourceCode' in subDict.keys():
        return False
    if not 'assertion' in subDict.keys():
        return False
    if not 'timeLimit' in subDict.keys():
        return False
    if not 'memoryLimit' in subDict.keys():
        return False
    return True


def checkCodegenValidity(subDict: dict):
    if not 'inputSourceCode' in subDict.keys():
        return False
    if not 'inputContent' in subDict.keys():
        return False
    if not 'outputCode' in subDict.keys():
        return False
    if not 'outputContent' in subDict.keys():
        return False
    if not 'timeLimit' in subDict.keys():
        return False
    if not 'memoryLimit' in subDict.keys():
        return False
    return True
