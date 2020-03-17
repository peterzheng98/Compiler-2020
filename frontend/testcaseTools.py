import json
import requests
import os
import base64
from tqdm import tqdm


if __name__ == '__main__':
    file_list_path = '/Users/peterzheng/Documents/Projects/OldProject/Compiler/Compiler 2020/testcase/sema/judgelist.txt'
    static_folder = '/Users/peterzheng/Documents/Projects/OldProject/Compiler/Compiler 2020/frontend/userInterface/src/static/testsets/'
    request_addr = 'http://127.0.0.1:43010/addDataSemantic'
    files_all = open(file_list_path, 'r').readlines()
    files_all = [i.strip('\n') for i in files_all]
    # for semantic
    bar = tqdm(desc='Progress', total=len(files_all))
    for file in files_all:
        if '/' in file:
            real_file = file.split('/')[-1]
        else:
            real_file = file
        caseData = open(os.path.join('/Users/peterzheng/Documents/Projects/OldProject/Compiler/Compiler 2020/testcase/sema/', file), 'r').readlines()
        caseData = [i.strip('\n') for i in caseData]
        metaIdx = (caseData.index('/*'), caseData.index('*/'))
        metaArea = caseData[metaIdx[0] + 1: metaIdx[1]]
        metaArea = [i.split(': ') for i in metaArea]
        metaDict = {i[0]: i[1] for i in metaArea}
        expectedResult = metaDict['Verdict'] == 'Success'
        dataArea = '\n'.join(caseData[metaIdx[1] + 1:])
        dataArea = base64.b64encode(dataArea.encode()).decode()
        send_package = {
            'source_code': dataArea,
            'assertion': True if expectedResult else False,
            'time_limit': 15.0,
            'inst_limit': -1,
            'memory_limit':512,
            'testcase': real_file
        }
        r = requests.post(request_addr, data=json.dumps(send_package), timeout=5)
        open(os.path.join(static_folder, real_file), 'w').write(dataArea)
        bar.update()
