from .ConfigDeploy import Config_Dict
import subprocess


def updateRepo(userCompilerLocalPath: str, lastHash: tuple, repoPath: str, uuid: str):
    cmd = ''
    commandResult = None
    timeout = Config_Dict['GitTimeout'] * 4
    if lastHash[0] != 1:  # no previous build or error occurred
        cmd = 'rm -rf * && git init && git remote add origin %s && git pull origin master' % repoPath
    else:
        archiveFileName = '%s.zip' % lastHash[1]
        backupPath = Config_Dict['compilerBackupPath'] + '/' + uuid + '/'
        cmd = 'zip -9 -r %s . && cp %s %s && rm %s && git pull -f' % (
            archiveFileName, archiveFileName, backupPath, archiveFileName)
    try:
        commandResult = subprocess.Popen(cmd, cwd=userCompilerLocalPath, stderr=subprocess.STDOUT,
                                         stdout=subprocess.PIPE, shell=True)
        start_time = time.time()
        while True:
            if commandResult.poll() is not None:
                break
            seconds_passed = time.time() - start_time
            if timeout and seconds_passed > timeout:
                commandResult.terminate()
                raise Exception()
            time.sleep(0.1)
    except Exception as identifier:
        return 1, "Timeout"
        pass
    return 0, commandResult.stdout.read().decode()


def getGitHash(pathORurl: str):
    '''
    Input: path
    Returns: Tuple<int, str> -> int: 1 Success 2 Error
    '''
    gitcmd = 'git ls-remote %s | grep heads/master' % pathORurl
    version = []
    try:
        version = subprocess.check_output(gitcmd, shell=True, timeout=Config_Dict['GitTimeout']).decode().strip().split(
            '\t')
        if len(version[0]) != 40:
            return 2, 'Length error, received [%s] with raw [%s]' % (version[0], '\t'.join(version))
        return 1, version[0]
    except subprocess.TimeoutExpired as identifier:
        return 2, 'Git Timeout: %s' % identifier
    except Exception as identifier:
        return 2, 'Exception: %s' % identifier
