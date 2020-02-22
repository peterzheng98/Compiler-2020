import subprocess


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
