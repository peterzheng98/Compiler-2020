from ConfigDeploy import Config_Dict
from initalSet import initDatabase
from validityCheck import checkValidWorkList, checkSemanticValidity, checkCodegenValidity
from dockerTools import existImage, cleanDocker, makeContainer, C
from judgeTools import judgeSemantic, judgeCodeGen, judgeSemantic_local_adapter
from gitTools import updateRepo, getGitHash, fetchGitCommit
import sys
import docker
import requests
import json
import time
import os
import shutil
import time
import subprocess

from coreModule import build_compiler, build_compiler_local, build_compiler_local_adapter

localdataVersion = None
original_user = []


def genLog(s: str):
    timeStr = ''
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(time.time()))
        f.write('[%s] %s\n' % (timeStr, s))
    print('[{}] {}'.format(timeStr, s))


def resetAll():
    cleanDocker()
    pass


'''
Command Arguments:
    clean: clean all the docker
    reset: clean all the data and docker
    run: normally run
'''
if __name__ == '__main__':
    if len(sys.argv) != 1 and len(sys.argv) != 2:
        print('Error in arguments. Vaild arguments are clean, reset.')
        exit(0)
    if len(sys.argv) == 2 and sys.argv[1] == 'clean':
        cleanDocker()
    elif len(sys.argv) == 2 and sys.argv[1] == 'reset':
        resetAll()
    elif len(sys.argv) == 2:
        print('Error in arguments. Vaild arguments are clean, reset.')
        exit(0)

    print('Ready to judge')
    while True:
        r = None
        try:
            # ---------------Server Build Task Started------------------
            r = requests.get(Config_Dict['serverFetchCompileTask'], timeout=2)
            r.raise_for_status()
            build_task_Dict = r.json()
            genLog(' Build Stage Task: {}'.format(build_task_Dict))
            if build_task_Dict['code'] == 200:
                genLog('Build Task received: {}'.format(build_task_Dict['message']))
                build_task = build_task_Dict['message']
                verdict, GitHash, GitCommit, BuildMessage, useless = build_compiler_local_adapter(build_task)
                build_task['verdict'] = verdict
                build_task['gitHash'] = GitHash
                build_task['gitCommit'] = GitCommit
                build_task['message'] = BuildMessage
                genLog('(Build result) {}'.format(build_task))
                r = requests.post(Config_Dict['serverSubmitCompileTask'], timeout=2, data=json.dumps(build_task))
                while r.json()['code'] != 200:
                    time.sleep(1)
                    r = requests.post(Config_Dict['serverSubmitCompileTask'], timeout=2, data=json.dumps(build_task))
                continue
            time.sleep(1)
            # ---------------Server Fetch Build Ended-------------------

            # ---------------Server Fetch Task Started------------------
            r = requests.get(Config_Dict['serverFetchTask'], timeout=10)
            r.raise_for_status()
            task_Dict = r.json()
            genLog(' Judge Stage Task: {}'.format(task_Dict))
            if task_Dict['code'] == 404:  # 1 for sleep
                genLog('  Nothing can be done currently.')
                continue
            if task_Dict['code'] == 200:
                genLog(' Accept work %s, contains %d subwork.' % (task_Dict['workid'], len(task_Dict['target'])))
                subtask_List = task_Dict['target']
                # Assert whether the data is valid
                validresult_Bool = checkValidWorkList(subtask_List)
                if not validresult_Bool:
                    genLog('(checkValidity Failed) Work:{}'.format(task_Dict['workid']))
                    continue
                submitResult_list = []
                for subtask_dict in subtask_List:
                    genLog('(Judge)  Judging: uuid:%s, repo:%s, stage:%d' % (
                        subtask_dict['uuid'], subtask_dict['repo'], subtask_dict['stage']))
                    build_task = {
                        'uuid': subtask_dict['uuid'],
                        'repo': subtask_dict['repo']
                    }
                    verdict, GitHash, GitCommit, BuildMessage, imageName = build_compiler_local(build_task)

                    # build image finish
                    # here we can confirm that image must exists
                    # next we should get the type of the judging protocol
                    subtaskResult_dict = {}
                    if subtask_dict['stage'] == 1:  # semantic check
                        checkResult = checkSemanticValidity(subtask_dict)
                        if not checkResult:
                            genLog('(checkSemanticValidity Failed) subWorkId:{}'.format(subtask_dict['subWorkId']))
                            continue
                        judgeResult = ['', '']
                        subtask_dict['imagename'] = imageName
                        judgeResult[0], judgeResult[1], time_interval = judgeSemantic_local_adapter(subtask_dict)
                        subtaskResult_dict['subWorkId'] = subtask_dict['subWorkId']
                        subtaskResult_dict['JudgeResult'] = judgeResult
                        subtaskResult_dict['Judger'] = Config_Dict['judgerName']
                        subtaskResult_dict['JudgeTime'] = '{:.6f}/0/{}'.format(time_interval,
                                                                               time.strftime('%Y.%m.%d %H:%M:%S',
                                                                                             time.localtime(
                                                                                                 time.time())))
                        subtaskResult_dict['testCase'] = subtask_dict['testCase']
                        subtaskResult_dict['judgetype'] = subtask_dict['stage']
                        subtaskResult_dict['uuid'] = subtask_dict['uuid']
                        subtaskResult_dict['git_hash'] = GitHash
                        subtaskResult_dict['taskID'] = subtask_dict['taskID']
                        subtaskResult_dict['test_case_id'] = subtask_dict['test_case_id']
                        submitResult_list.append(subtaskResult_dict)
                        genLog('(Judge-Semantic)  uuid={}, subWorkId={}, judgeResult={}, Time={}, testCaseId={}'.format(
                            subtask_dict['uuid'],
                            subtask_dict['subWorkId'],
                            judgeResult,
                            subtaskResult_dict['JudgeTime'],
                            subtaskResult_dict['testCase']
                        ))
                    elif subtask_dict['stage'] == 2 or subtask_dict['stage'] == 3:
                        checkResult = checkCodegenValidity(subtask_dict)
                        if not checkResult:
                            genLog('(checkCodegenValidity Failed) subWorkId:{}'.format(subtask_dict['subWorkId']))
                            continue
                        judgeResult = ['', '']
                        subtask_dict['imagename'] = imageName
                        judgeResult[0], judgeResult[1], time_interval, execution_cycle = judgeCodeGen(subtask_dict)
                        subtaskResult_dict['subWorkId'] = subtask_dict['subWorkId']
                        subtaskResult_dict['JudgeResult'] = judgeResult
                        subtaskResult_dict['Judger'] = Config_Dict['judgerName']
                        subtaskResult_dict['JudgeTime'] = '{:.6f}/{}/{}'.format(time_interval, execution_cycle,
                                                                                time.strftime('%Y.%m.%d %H:%M:%S',
                                                                                              time.localtime(time.time())))
                        subtaskResult_dict['testCase'] = subtask_dict['testCase']
                        subtaskResult_dict['judgetype'] = subtask_dict['stage']
                        subtaskResult_dict['uuid'] = subtask_dict['uuid']
                        subtaskResult_dict['git_hash'] = GitHash
                        subtaskResult_dict['taskID'] = subtask_dict['taskID']
                        subtaskResult_dict['test_case_id'] = subtask_dict['test_case_id']
                        submitResult_list.append(subtaskResult_dict)
                        genLog(
                            '(Judge-Codegen/Optimize)  uuid={}, subWorkId={}, judgeResult={}, Time={}, testCaseId={}'.format(
                                subtask_dict['uuid'],
                                subtask_dict['subWorkId'],
                                judgeResult,
                                subtaskResult_dict['JudgeTime'],
                                subtaskResult_dict['testCase']
                            ))
                    else:
                        # TODO: error, the stage not supported.
                        genLog('(Judge-Unknown)  uuid={}, subWorkId={}, Not supported stage={}'.format(
                            subtask_dict['uuid'],
                            subtask_dict['subWorkId'],
                            subtask_dict['stage']
                        ))
                        pass
                # submit the result to the server and wait for next
                while True:
                    try:
                        r = requests.post(url=Config_Dict['serverSubmitTask'],
                                          data=json.dumps(submitResult_list, ensure_ascii=False))
                        if r.json()['code'] == 200:
                            genLog('(Judge-Submit)  Sent!')
                            break
                        genLog('(Judge-Submit)  Not sent! Retry after 1s.')
                        time.sleep(1)  # If not success, resend after 1s
                    except Exception as identifier:
                        genLog('(Judge-Submit)  Error occurred! Retry after 1s. {}'.format(identifier))
                        time.sleep(1)
                        continue
                        pass
        except requests.exceptions.ConnectTimeout as identifier:
            print('  -> Connection Timeout with %s, retrying' % identifier)
            genLog('  Connection Timeout with %s' % identifier)
            continue
            pass
        except requests.exceptions.HTTPError as identifier:
            print('  -> HTTP Error with %s, exiting' % identifier)
            genLog('   HTTP Error with %s' % identifier)
            exit(0)
        except Exception as identifier:
            print('  Unknown Error occurred with %s' % identifier)
            genLog('   UnknownError: %s' % identifier)
            continue
