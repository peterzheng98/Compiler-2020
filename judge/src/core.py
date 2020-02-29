from ConfigDeploy import Config_Dict
from initalSet import initDatabase
from validityCheck import checkValidWorkList, checkSemanticValidity, checkCodegenValidity
from dockerTools import existImage, cleanDocker, makeContainer, C
from judgeTools import judgeSemantic, judgeCodeGen
from .gitTools import updateRepo, getGitHash, fetchGitCommit
import sys
import docker
import requests
import json
import time
import os
import shutil
import time
import subprocess

localdataVersion = None
original_user = []


def genLog(s: str):
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(time.time()))
        f.write('[%s] %s\n' % (timeStr, s))


def build_compiler(config_dict: dict):
    assert 'uuid' in config_dict.keys()
    assert 'repo' in config_dict.keys()
    userCompilerPath = Config_Dict['compilerPath'] + '/' + config_dict['uuid']
    # Check the hash value
    # 1. get local hash
    hashResultLocal = getGitHash(userCompilerPath)
    # 2. get remote hash
    hashResultRemote = getGitHash(config_dict['repo'])
    hashMatched = (hashResultLocal[0] == 1 and hashResultRemote[0] == 1 and hashResultLocal[1] ==
                   hashResultRemote[1])
    genLog('(build_compiler)Judging:local:%s, remote:%s, matched:%s' % (hashResultLocal, hashResultRemote, hashMatched))
    # if not matched -> save a duplicated copy of the last version
    # not matched: update the repo
    if not hashMatched:
        updateRepo(userCompilerPath, hashResultLocal, config_dict['repo'], config_dict['uuid'])
    # Matched -> check whether the image exists
    # Not matched -> build images
    # dockerimage:uuid + hash[0:8]
    imageName = Config_Dict['dockerprefix'] + config_dict['uuid'] + '_' + hashResultRemote[1][0:8]
    task_Dict['imagename'] = imageName
    if (not hashMatched) or (not existImage(imageName)):
        build_result = 'Not Available'
        # copy files to temporary
        _ = subprocess.Popen('mkdir temp && cp {}/* temp/'.format(userCompilerPath), cwd=)
        try:
            with open('temp/Dockerfile', 'w') as f:
                f.write(
                    'FROM %s\nADD %s /compiler\nWORKDIR /compiler\nRUN bash /compiler/build.bash' % (
                        Config_Dict['dockerprefix'] + 'base',
                        Config_Dict['compilerPath'] + '/' + subtask_dict['uuid']))
            image_built = C.images.build(path='./temp/', rm=True, tag=imageName)
        except docker.errors.BuildError as identifier:
            genLog('(Judge-Build)  Built Error occurred. target:%s -> %s' % (subtask_dict, identifier))
        except Exception as identifier:
            genLog(
                '(Judge-Build)  Unknown Error occurred. target:%s -> %s' % (subtask_dict, identifier))
        shutil.rmtree('./temp')
        genLog('(Judge-Build)  built finished. target:%s' % subtask_dict)
        # Check whether the images exists.
        if existImage(imageName):
            genLog('(Judge-Build)  check existed = ok, name = %s' % imageName)
            gitCommitLog = fetchGitCommit(userCompilerPath, hashResultRemote[1])
            return 'Success', hashResultRemote[1], gitCommitLog, build_result
        else:
            genLog('(Judge-Build)  check existed = failed, name = %s' % imageName)
            gitCommitLog = fetchGitCommit(userCompilerPath, hashResultRemote[1])
            return 'Fail', hashResultRemote[1], gitCommitLog, build_result
    else:
        # matched and exist
        # verdict, GitHash, GitCommit, BuildMessage
        log = fetchGitCommit(userCompilerPath, hashResultRemote[1])
        return 'Success', hashResultRemote[1], log, 'Recently built.'


def updateUserList(userlist_Dict: dict):
    olduserList_Dict = {}
    updateList = []
    insertList = []
    ## There will be no remove strategies.
    for uuid, repo in userlist_Dict.items():
        ## If the user does not exists, insert the data
        if uuid not in olduserList_Dict.keys():
            insertList.append((uuid, repo))
        elif olduserList_Dict[uuid] != repo:
            updateList.append((uuid, repo))
        original_user.append(uuid.copy())
    genLog('(UpdateUser) Total Insertion: %d, Total Modification: %d' % (len(insertList), len(updateList)))
    for i in updateList:
        genLog('(UpdateUser) Modification: %s' % i)
        uuid = i[0]
        if not os.path.exists(Config_Dict['compilerPath'] + '/' + uuid):
            os.makedirs(Config_Dict['compilerPath'] + '/' + uuid)
        else:
            shutil.rmtree(Config_Dict['compilerPath'] + '/' + uuid)
            genLog('(UpdateUser)     Folder with uuid %s not null, remove it and create an empty one.' % uuid)
            os.makedirs(Config_Dict['compilerPath'] + '/' + uuid)

        if not os.path.exists(Config_Dict['compilerBackupPath'] + '/' + uuid):
            os.makedirs(Config_Dict['compilerBackupPath'] + '/' + uuid)
        else:
            shutil.rmtree(Config_Dict['compilerBackupPath'] + '/' + uuid)
            genLog('(UpdateUser)     Folder(Backup) with uuid %s not null, remove it and create an empty one.' % uuid)
            os.makedirs(Config_Dict['compilerBackupPath'] + '/' + uuid)
    for i in insertList:
        genLog('(UpdateUser) Insertion: %s' % i)
        uuid = i[0]
        ## make dir for the user.
        if not os.path.exists(Config_Dict['compilerPath'] + '/' + uuid):
            os.makedirs(Config_Dict['compilerPath'] + '/' + uuid)
        else:
            shutil.rmtree(Config_Dict['compilerPath'] + '/' + uuid)
            genLog('(UpdateUser)     Folder with uuid %s not null, remove it and create an empty one.' % uuid)
            os.makedirs(Config_Dict['compilerPath'] + '/' + uuid)
    genLog('(UpdateUser) Finished')
    pass


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
    print('Preparation: Fetch the user repo list')
    genLog('Preparation: Fetch the user repo list')
    # Fetch the user repo list and update
    url = Config_Dict['serverFetchUser']
    r = requests.get(url)
    userList_Dict = r.json()
    RetryCount = 0
    while len(userList_Dict) == 0 or userList_Dict['code'] != 200:
        print('Retry #{}: Request again after 1s. Last receive: {}'.format(RetryCount, userList_Dict))
        genLog('Retry #{}: Request again after 1s. Last receive: {}'.format(RetryCount, userList_Dict))
        time.sleep(1)
        url = Config_Dict['serverFetchUser']
        r = requests.get(url)
        userList_Dict = r.json()
        RetryCount = RetryCount + 1
    userList_Dict = userList_Dict['message']
    print('  User list fetched, %d records.' % (len(userList_Dict)))
    genLog('=' * 20 + '\nUser list fetched, %d records.' % (len(userList_Dict)))
    for k, v in userList_Dict.items():
        genLog('(User) %s - %s' % (k, v))
    genLog('=' * 20)
    # Update the database
    updateUserList(userList_Dict)
    genLog('=' * 20)
    genLog('  Check base container')
    imageLists = C.images.list()
    imageTags = [i.tags for i in imageLists]
    if (Config_Dict['dockerprefix'] + 'base') in imageTags:
        print('  Base image detected!')
    else:
        genLog('  Make base container')
        result = makeContainer(Config_Dict['dockerbasepath'], Config_Dict['dockerprefix'] + 'base')
        if not result[0]:
            genLog('Error: Make base container failed!')
            genLog(result[1])
            print('Make base container failed, check the output log')
            exit(0)

    print('Ready to judge')
    while True:
        r = None
        try:
            r = requests.get(Config_Dict['serverFetchCompileTask'], timeout=2)
            r.raise_for_status()
            build_task_Dict = r.json()
            if build_task_Dict['code'] == 200:
                genLog('Build Task received: {}'.format(build_task_Dict['message']))
                build_task = build_task_Dict['message']
                verdict, GitHash, GitCommit, BuildMessage = build_compiler(build_task)
                build_task['verdict'] = verdict
                build_task['gitHash'] = GitHash
                build_task['gitCommit'] = GitCommit
                build_task['message'] = BuildMessage
                r = requests.post(Config_Dict['serverSubmitCompileTask'], timeout=2, data=json.dumps(build_task))
                while r.json()['code'] != 200:
                    time.sleep(1)
                    r = requests.post(Config_Dict['serverSubmitCompileTask'], timeout=2, data=json.dumps(build_task))
                continue

            time.sleep(1)
            r = requests.get(Config_Dict['serverFetchTask'], timeout=10)
            r.raise_for_status()
            task_Dict = r.json()
            if task_Dict['code'] == 1:  # 1 for sleep
                genLog('  Nothing can be done currently.')
                continue
            if task_Dict['code'] == 2:
                genLog(' Accept work %s, contains %d subwork.' % (task_Dict['workid'], len(task_Dict['target'])))
                if 'newUser' in task_Dict.keys() and len(task_Dict['newUser']) != 0:
                    corSet = set(original_user)
                    addRequest = {}
                    for uuid, repo in task_Dict['newUser'].items():
                        if uuid not in corSet:
                            addRequest[uuid] = repo
                    if len(addRequest) != 0:
                        print('  User list updated, %d records.' % (len(userList_Dict)))
                        genLog('=' * 20 + '\nUser list fetched, %d records.' % (len(userList_Dict)))
                        for k, v in userList_Dict.items():
                            genLog('(User) %s - %s' % (k, v))
                        genLog('=' * 20)
                        # Update the database
                        updateUserList(addRequest)
                        genLog('=' * 20)
                subtask_List = task_Dict['target']
                # Assert whether the data is valid
                validresult_Bool = checkValidWorkList(subtask_List)
                if not validresult_Bool:
                    # TODO: return false result
                    continue
                submitResult_list = []
                for subtask_dict in subtask_List:
                    genLog('(Judge)  Judging: uuid:%s, repo:%s, stage:%d' % (
                        subtask_dict['uuid'], subtask_dict['repo'], subtask_dict['stage']))
                    userCompilerPath = Config_Dict['compilerPath'] + '/' + subtask_dict['uuid']
                    # Check the hash value
                    # 1. get local hash
                    hashResultLocal = getGitHash(userCompilerPath)
                    # 2. get remote hash
                    hashResultRemote = getGitHash(subtask_dict['repo'])
                    hashMatched = (hashResultLocal[0] == 1 and hashResultRemote[0] == 1 and hashResultLocal[1] ==
                                   hashResultRemote[1])
                    genLog('(Judge)    Judging:local:%s, remote:%s, matched:%s' % (
                        hashResultLocal, hashResultRemote, hashMatched))
                    # if not matched -> save a duplicated copy of the last version
                    # this is a todo function
                    # not matched: update the repo
                    if not hashMatched:
                        updateRepo(userCompilerPath, hashResultLocal, subtask_dict['repo'], subtask_dict['uuid'])
                    # Matched -> check whether the image exists
                    # Not matched -> build images
                    # dockerimage:uuid[0:8] + hash[0:8]
                    imageName = Config_Dict['dockerprefix'] + subtask_dict['uuid'] + '_' + hashResultRemote[1]
                    task_Dict['imagename'] = imageName
                    if (not hashMatched) or (not existImage(imageName)):
                        # copy files to temporary
                        _ = subprocess.Popen('mkdir temp && cp %s/* temp/')
                        try:
                            with open('temp/Dockerfile', 'w') as f:
                                f.write(
                                    'FROM %s\nADD %s /compiler\nWORKDIR /compiler\nRUN bash /compiler/build.bash' % (
                                        Config_Dict['dockerprefix'] + 'base',
                                        Config_Dict['compilerPath'] + '/' + subtask_dict['uuid']))
                            image_built = C.images.build(path='./temp/', rm=True, tag=imageName)
                        except docker.errors.BuildError as identifier:
                            genLog('(Judge-Build)  Built Error occurred. target:%s -> %s' % (subtask_dict, identifier))
                            continue
                        except Exception as identifier:
                            genLog(
                                '(Judge-Build)  Unknown Error occurred. target:%s -> %s' % (subtask_dict, identifier))
                            continue
                        shutil.rmtree('./temp')
                        genLog('(Judge-Build)  built finished. target:%s' % subtask_dict)
                        # Check whether the images exists.
                        if existImage(imageName):
                            genLog('(Judge-Build)  check existed = ok, name = %s' % imageName)
                        else:
                            genLog('(Judge-Build)  check existed = failed, name = %s' % imageName)
                    # build image finish
                    # here we can confirm that image must exists
                    # next we should get the type of the judging protocol
                    subtaskResult_dict = {}
                    if subtask_dict['stage'] == 1:  # semantic check
                        checkResult = checkSemanticValidity(subtask_dict)
                        if not checkResult:
                            # TODO: return false
                            continue
                        judgeResult = judgeSemantic(subtask_dict)
                        subtaskResult_dict['subWorkId'] = subtask_dict['subWorkId']
                        subtaskResult_dict['JudgeResult'] = judgeResult
                        subtaskResult_dict['Judger'] = Config_Dict['judgerName']
                        subtaskResult_dict['JudgeTime'] = time.strftime('%Y.%m.%d %H:%M:%S',
                                                                        time.localtime(time.time()))
                        subtaskResult_dict['testCase'] = subtask_dict['testCase']
                        subtaskResult_dict['judgetype'] = subtask_dict['stage']
                        subtaskResult_dict['uuid'] = subtask_dict['uuid']
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
                            # TODO: return false
                            continue
                        judgeResult = judgeCodeGen(subtask_dict)
                        subtaskResult_dict['subWorkId'] = subtask_dict['subWorkId']
                        subtaskResult_dict['JudgeResult'] = judgeResult
                        subtaskResult_dict['Judger'] = Config_Dict['judgerName']
                        subtaskResult_dict['JudgeTime'] = time.strftime('%Y.%m.%d %H:%M:%S',
                                                                        time.localtime(time.time()))
                        subtaskResult_dict['testCase'] = subtask_dict['testCase']
                        subtaskResult_dict['judgetype'] = subtask_dict['stage']
                        subtaskResult_dict['uuid'] = subtask_dict['uuid']
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
                        if r.json()['result'] == 'ok':
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
