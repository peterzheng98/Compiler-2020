import subprocess
import time


def genLogInGit(s: str):
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(time.time()))
        f.write('[%s] %s\n' % (timeStr, s))


def getGitHash(pathORurl: str):
    '''
    Input: path
    Returns: Tuple<int, str> -> int: 1 Success 2 Error
    '''
    gitcmd = 'git ls-remote %s | grep heads/master' % pathORurl
    version = []
    try:
        version = subprocess.check_output(gitcmd, shell=True, timeout=2).decode().strip().split('\t')
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
        log = 'commit' + stdout_git_log[stdout_git_log.index(gitHash[1])]
    except Exception as identifier:
        genLogInGit('Error when matching existing repo: {}'.format(identifier))
    return log
