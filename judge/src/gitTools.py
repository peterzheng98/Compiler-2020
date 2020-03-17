from ConfigDeploy import Config_Dict
import subprocess
import time


def updateRepo(userCompilerLocalPath: str, lastHash: tuple, repoPath: str, uuid: str):
    cmd = ''
    commandResult = None
    timeout = Config_Dict['GitTimeout']
    commandResult = None
    if lastHash[0] != 1:  # no previous build or error occurred
        cmd = 'rm -rf * && rm -rf .git && git clone {} .'.format(repoPath)
    else:
        cmd = 'rm -rf * && rm -rf .git && git clone {} .'.format(repoPath)
    try:
        commandResult = subprocess.Popen(cmd, cwd=userCompilerLocalPath, stderr=subprocess.STDOUT,
                                         stdout=subprocess.PIPE, shell=True)
        commandResult.wait(timeout)
    except subprocess.TimeoutExpired as identifier:
        commandResult.terminate()
        return 1, "Timeout"
    except Exception as identifier:
        return 1, "Runtime Error: {}".format(identifier)
    return 0, commandResult.stdout.read().decode()


def getGitHash(pathORurl: str):
    '''
    Input: path
    Returns: Tuple<int, str> -> int: 1 Success 2 Error
    '''
    gitcmd = 'git ls-remote %s | grep heads/master' % pathORurl
    version = []
    try:
        version = subprocess.check_output(gitcmd, shell=True, timeout=30).decode().strip().split(
            '\t')
        if len(version[0]) != 40:
            return 2, 'Length error, received [%s] with raw [%s]' % (version[0], '\t'.join(version))
        return 1, version[0]
    except subprocess.TimeoutExpired as identifier:
        return 2, 'Git Timeout: %s' % identifier
    except Exception as identifier:
        return 2, 'Exception: %s' % identifier


def fetchGitCommit(repoPath: str, gitHash: str) -> str:
    git_log = subprocess.Popen(["git", "log"], cwd=repoPath, stdout=subprocess.PIPE, shell=False)
    log = 'Unavailable'
    try:
        git_log.wait(2)
        stdout_git_log = git_log.stdout.readlines()
        stdout_git_log = ''.join([i.decode() for i in stdout_git_log]).split('commit')
        idx = 0
        for i, s in enumerate(stdout_git_log):
            if gitHash in s:
                idx = i
                break
        log = 'commit' + stdout_git_log[idx]
    except Exception as identifier:
        genLogInGit('Error when matching existing repo: {}'.format(identifier))
    return log


def genLogInGit(s: str):
    timeStr = ''
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(time.time()))
        f.write('[%s] %s\n' % (timeStr, s))
    print('[{}] {}'.format(timeStr, s))
