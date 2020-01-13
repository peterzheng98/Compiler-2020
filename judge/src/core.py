from ConfigDeploy import Config_Dict
from initial import initDatabase
import sys
import docker
import requests
import json
import time
import pymysql.cursors
import pymysql
import os
import shutil
import time
import subprocess

C = docker.from_env()
sqlConnector = None
sqlCursor = None
localdataVersion = None

def existImage(imageName):
    try:
        C.images.get(imageName)
        return True
    except docker.errors.ImageNotFound as identifier:
        return False
    except Exception:
        return False
    

def updateRepo(userCompilerLocalPath: str, lastHash: tuple, repoPath: str, uuid: str):
    cmd = ''
    commandResult = None
    timeout = Config_Dict['GitTimeout'] * 4
    if lastHash[0] != 1: # no previous build or error occurred
        cmd = 'rm -rf * && git init && git remote add origin %s && git pull origin master' % repoPath
    else:
        archiveFileName = '%s.zip' % lastHash[1]
        backupPath = Config_Dict['compilerBackupPath'] + '/' + uuid + '/'
        cmd = 'zip -9 -r %s . && cp %s %s && rm %s && git pull -f' % (archiveFileName, archiveFileName, backupPath, archiveFileName)
    try:
        commandResult = subprocess.Popen(cmd, cwd=userCompilerLocalPath, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        start_time = time.time()
        while True:
            if commandResult.poll() is not None:
                break
            seconds_passed = time.time() - t_beginning 
            if timeout and seconds_passed > timeout: 
                commandResult.terminate() 
                raise Exception()
            time.sleep(0.1) 
    except Exception as identifier:
        return (1, "Timeout")
        pass
    return (0, commandResult.stdout.read().decode())



def checkValidWorkList(worklist: list):
    for work in worklist:
        if not 'uuid' in work.items():
            return False
        if not 'repo' in work.items():
            return False
        if not 'testcase' in work.items():
            return False
        if not 'stage' in work.items():
            return False
    return True


def getGitHash(pathORurl: str):
    '''
    Input: path
    Returns: Tuple<int, str> -> int: 1 Success 2 Error
    '''
    gitcmd = 'git ls-remote %s | grep heads/master' % pathORurl
    version = []
    try:
        version = subprocess.check_output(gitcmd, shell=True, timeout=Config_Dict['GitTimeout']).decode().strip().split('\t')
        if len(version[0]) != 40:
            return (2, 'Length error, received [%s] with raw [%s]' % (version[0], '\t'.join(version)))
        return (1, version[0])
    except subprocess.TimeoutExpired as identifier:
        return (2, 'Git Timeout: %s' % identifier)
    except Exception as identifier:
        return (2, 'Exception: %s' % identifier)
    

def makeContainer(dockerfilePath: str, imageName: str):
    try:
        imagesbuilt_Tuple = C.images.build(dockerfile=dockerfilePath, tag=imageName)
        return (True, imagesbuilt_Tuple[1], imagesbuilt_Tuple[0])
    except Exception as identifier:
        return (False, 'An error in executing makeContainer(%s, %s) in core.py. [%s]' % (dockerfilePath, imageName, identifier))
        pass

def genLog(s: str):
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S',time.localtime(time.time()))
        f.write('[%s] %s\n'%(timeStr, s))

def cleanDocker():
    '''
    Clean all the existing docker. Except for the base docker.
    The dockerPrefix is set in ConfigDeploy.
    '''
    ImageLists = C.images.list()
    for image in ImageLists:
        C.images.remove(image=image.tags)
    pass

def updateUserList(userlist_Dict: dict):
    sqlCommand = 'SELECT uuid, repo FROM userInfo'
    sqlCursor.execute(sqlCommand)
    olduserList_Dict = {}
    for row in sqlCursor.fetchall():
        olduserList_Dict[row[0]] = row[1]
    updateList = []
    insertList = []
    ## There will be no remove strategies.
    for uuid, repo in userlist_Dict.items():
        ## If the user does not exists, insert the data
        if uuid not in olduserList_Dict.keys():
            insertList.append((uuid, repo))
        elif olduserList_Dict[uuid] != repo:
            updateList.append((uuid, repo))
    genLog('(UpdateUser) Total Insertion: %d, Total Modification: %d' % (len(insertList), len(updateList)))
    for i in updateList:
        genLog('(UpdateUser) Modification: %s' % i)
        sqlCommand = 'UPDATE userInfo SET repo=\'%s\', lastBuild=to_date(\'1970-01-01 00:00:00\', \'yyyy-mm-dd hh24:mi:ss\'), status=\'No previous build\', verdict=\' \' WHERE uuid=\'%s\''
        genLog('(UpdateUser)    Modification SQL Comannd: %s' % (sqlCommand % (i[1], i[0])))
        sqlCursor.execute(sqlCommand % (i[1], i[0]))
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
        sqlConnector.commit()
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
        sqlCommand = 'INSERT INTO userInfo (uuid, repo, lastBuild, status) VALUES (\'%s\', \'%s\', \'1970-01-01 00:00:00\' \'No previous build\')'
        genLog('(UpdateUser)    Insertion SQL Comannd: %s' % (sqlCommand % i))
        sqlCursor.execute(sqlCommand % (i[0], i[1]))
        sqlConnector.commit()
    genLog('(UpdateUser) Finished')
    pass


def resetAll():
    cleanDocker()
    Connector = pymysql.Connect(
        host=Config_Dict['sqladdress'], 
        port=Config_Dict['sqlport'],
        user=Config_Dict['sqlname'],
        passwd=Config_Dict['sqlword']
    )
    cursor = Connector.cursor()
    sqlcommand = 'drop database if exists %s;' % (Config_Dict['sqltable'])
    cursor.executr(sqlcommand)
    Connector.commit()
    print('Database %s deleted!' % (Config_Dict['sqltable']))
    initDatabase()
    cursor.close()
    Connector.close()
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
    print('Connecting to the database')
    genLog('Connecting to the database')
    sqlConnector = pymysql.Connect(
        host=Config_Dict['sqladdress'], 
        port=Config_Dict['sqlport'],
        user=Config_Dict['sqlname'],
        passwd=Config_Dict['sqlword']
    )
    sqlCursor = Connector.cursor()
    print('Database Connected')
    genLog('Database Connected')
    print('Preparation: Fetch the user repo list')
    genLog('Preparation: Fetch the user repo list')
    ## Fetch the user repo list and update 
    url = Config_Dict['serverFetchUser']
    r = requests.get(url)
    userlist_Dict = r.json()
    print('  User list fetched, %d records.' % (len(userList)))
    genLog('=' * 20 + '\nUser list fetched, %d records.' % (len(userList)))
    for k, v in userlist_Dict.items():
        genLog('(User) %s - %s' % (k, v))
    genLog('=' * 20)
    ## Update the database
    updateUserList(userlist_Dict)
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
    # genLog('  Generating Image Templates')
    # with open(Config_Dict['dockerfilepath'] + 'template.dockerfile', 'w') as f:
    #     f.write('FROM %s\nADD %s /compiler\nWORKDIR /compiler\nRUN bash /compiler/build.bash' % (Config_Dict['dockerprefix'] + 'base', Config_Dict['compilerPath']))

    print('Ready to judge')
    while True:
        r = None
        try:
            time.sleep(1)
            r = requests.get(Config_Dict['serverFetchTask'], timeout=10)
            r.raise_for_status()
            task_Dict = r.json()
            if task_Dict['code'] == 1: # 1 for sleep
                genLog('  Nothing can be done currently.')
                continue
            if task_Dict['code'] == 2:
                genLog(' Accept work %s, contains %d subwork.' % (task_Dict['workid'], len(task_Dict['target'])))
                subtask_List = task_Dict['target']
                # Assert whether the data is valid
                validresult_Bool = checkValidWorkList(subtask_List)
                if not validresult_Bool:
                    # TODO: return false result
                    continue
                for subtask_dict in subtask_List:
                    genLog('(Judge)  Judging: uuid:%s, repo:%s, stage:%d' % (subtask_dict['uuid'], subtask_dict['repo'], subtask_dict['stage']))
                    userCompilerPath = Config_Dict['compilerPath'] + '/' + subtask_dict['uuid']
                    # Check the hash value
                    # 1. get local hash
                    hashResultLocal = getGitHash(userCompilerPath)
                    # 2. get remote hash
                    hashResultRemote = getGitHash(subtask_dict['repo'])
                    hashMatched = (hashResultLocal[0] == 1 and hashResultRemote[0] == 1 and hashResultLocal[1] == hashResultRemote[1])
                    genLog('(Judge)    Judging:local:%s, remote:%s, matched:%s' % (hashResultLocal, hashResultRemote, hashMatched))
                    # if not matched -> save a duplicated copy of the last version
                    # this is a todo function
                    # not matched: update the repo
                    if not hashMatched:
                        updateRepo(userCompilerPath, hashResultLocal, subtask_dict['repo'], subtask_dict['uuid'])
                    # Matched -> check whether the image exists
                    # Not matched -> build images
                    # dockerimage:uuid[0:8] + hash[0:8]
                    imageName = Config_Dict['dockerprefix'] + subtask_dict['uuid'] + '_' + hashResultRemote[1]
                    if (not hashMatched) or (not existImage(imageName)):
                        # copy files to temporary
                        _ = subprocess.Popen('mkdir temp && cp %s/* temp/')
                        try:
                            with open('temp/Dockerfile', 'w') as f:
                                f.write('FROM %s\nADD %s /compiler\nWORKDIR /compiler\nRUN bash /compiler/build.bash' % (Config_Dict['dockerprefix'] + 'base', Config_Dict['compilerPath'] + '/' + subtask_dict['uuid']))
                            image_built = C.images.build(path='./temp/', rm=True, tag=imageName)
                        except docker.errors.BuildError as identifier:
                            genLog('(Judge-Build)  Built Error occurred. target:%s -> %s' % (subtask_dict, identifier))
                            continue
                        except Exception as identifier:
                            genLog('(Judge-Build)  Unknown Error occurred. target:%s -> %s' % (subtask_dict, identifier))
                            continue
                        shutil.rmtree('./temp')
                        genLog('(Judge-Build)  built finished. target:%s' % subtask_dict)
                        # Check whether the images exists.
                        if existImage(imageName):
                            genLog('(Judge-Build)  check existed = ok, name = %s' % imageName)
                        else:
                            genLog('(Judge-Build)  check existed = failed, name = %s' % imageName)
                    # build image finish
                    
                    

                


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
    