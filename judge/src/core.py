from ConfigDeploy import Config_Dict
from initial import initDatabase
import sys
import docker
import requests
import json
import time
import pymysql.cursors
import pymysql


C = docker.from_env()
sqlConnector = None
sqlCursor = None

def genLog(s: str):
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S',time.localtime(time.time()))
        f.write('[%s] %s\n'%(timeStr, s))

def cleanDocker():
    '''
    Clean all the existing docker. Except for the base docker.
    The dockerPrefix is set in ConfigDeploy.
    '''
    containersList_List = C.containers.list(all=True)
    for container in containersList_List:
        if Config_Dict['dockerprefix'] in container.name:
            container.remove()
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
        sqlConnector.commit()
    for i in insertList:
        genLog('(UpdateUser) Insertion: %s' % i)
        uuid = i[0]
        dockername = Config_Dict['dockerprefix'] + uuid[:8]
        sqlCommand = 'INSERT INTO userInfo (uuid, repo, lastBuild, status, dockername) VALUES (\'%s\', \'%s\', \'1970-01-01 00:00:00\' \'No previous build\', \'%s\')'
        genLog('(UpdateUser)    Insertion SQL Comannd: %s' % (sqlCommand % i))
        sqlCursor.execute(sqlCommand % (i[0], i[1], dockername))
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
    clean: clean all the docker but will not rebuild the base docker
    reset: clean all the data and docker but will not modify the base docker
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
