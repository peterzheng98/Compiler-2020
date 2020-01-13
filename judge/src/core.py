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


C = docker.from_env()
sqlConnector = None
sqlCursor = None

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
        if not os.path.exists(Config_Dict['dataPath'] + '/' + uuid):
            os.makedirs(Config_Dict['dataPath'] + '/' + uuid)
        else:
            shutil.rmtree(Config_Dict['dataPath'] + '/' + uuid)
            genLog('(UpdateUser)     Folder with uuid %s not null, remove it and create an empty one.' % uuid)
            os.makedirs(Config_Dict['dataPath'] + '/' + uuid)
        sqlConnector.commit()
    for i in insertList:
        genLog('(UpdateUser) Insertion: %s' % i)
        uuid = i[0]
        ## make dir for the user.
        if not os.path.exists(Config_Dict['dataPath'] + '/' + uuid):
            os.makedirs(Config_Dict['dataPath'] + '/' + uuid)
        else:
            shutil.rmtree(Config_Dict['dataPath'] + '/' + uuid)
            genLog('(UpdateUser)     Folder with uuid %s not null, remove it and create an empty one.' % uuid)
            os.makedirs(Config_Dict['dataPath'] + '/' + uuid)
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
    url = Config_Dict['server'] + Config_Dict['serverFetchUser']
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
    genLog('  Generating Image Templates')
    with open(Config_Dict['dockerfilepath'] + 'template.dockerfile', 'r') as f:
        f.write('FROM %s\nADD compiler /compiler\nWORKDIR /compiler\nRUN bash /compiler/build.bash' % (Config_Dict['dockerprefix'] + 'base'))
    