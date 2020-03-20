from ConfigDeploy import Config_Dict
from dockerTools import existImage, cleanDocker, makeContainer, C
from gitTools import updateRepo, getGitHash, fetchGitCommit
import base64
import os
import time
import subprocess


def genLog(s: str):
    timeStr = ''
    with open('JudgeLog.log', 'a') as f:
        timeStr = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(time.time()))
        f.write('[%s] %s\n' % (timeStr, s))
    print('[{}] {}'.format(timeStr, s))


def build_compiler_local(config_dict: dict):
    assert 'uuid' in config_dict.keys()
    assert 'repo' in config_dict.keys()
    userCompilerPath = Config_Dict['compilerPath'] + '/' + config_dict['uuid']
    hashResultLocal = getGitHash(userCompilerPath)
    imageName = Config_Dict['dockerprefix'] + config_dict['uuid'] + ':' + hashResultLocal[1][0:8]
    log = fetchGitCommit(userCompilerPath, hashResultLocal[1])
    return 'Success', hashResultLocal[1], log, 'Recently built.', imageName


def build_compiler(config_dict: dict):
    assert 'uuid' in config_dict.keys()
    assert 'repo' in config_dict.keys()
    userCompilerPath = Config_Dict['compilerPath'] + '/' + config_dict['uuid']
    git_build_stdout = ''
    git_build_stderr = ''
    genLog('[coreModule.py] Generating repo with path: {}'.format(userCompilerPath))
    if not os.path.exists(userCompilerPath):
        os.makedirs(userCompilerPath)
        try:
            genLog('[coreModule.py] Start cloning object.')
            process = subprocess.Popen(['git', 'clone', config_dict['repo'], '.'], cwd=userCompilerPath,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait(Config_Dict['GitTimeout'])
            git_build_stdout = process.stdout.readlines()
            git_build_stdout = ''.join([i.decode() for i in git_build_stdout])
            git_build_stderr = process.stderr.readlines()
            git_build_stderr = ''.join([i.decode() for i in git_build_stderr])
        except subprocess.TimeoutExpired as identifier:
            git_build_stderr = 'Git Timeout'
            genLog('[coreModule.py] Git Timeout')
            process.terminate()
            return 'Fail', 'N/A', base64.b64encode('N/A'.encode()).decode(), base64.b64encode(
                git_build_stderr.encode()).decode(), ''
        except Exception as identifier:
            git_build_stderr = 'GitRuntime Error: {}'.format(identifier)
            genLog('[coreModule.py] {}'.format(git_build_stderr))
            return 'Fail', 'N/A', base64.b64encode('N/A'.encode()).decode(), base64.b64encode(
                git_build_stderr.encode()).decode(), ''
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
    imageName = Config_Dict['dockerprefix'] + config_dict['uuid'] + ':' + hashResultRemote[1][0:8]
    if (not hashMatched) or (not existImage(imageName)):
        build_result = 'Not Available'
        build_verdict = 'Fail'
        # copy files to temporary
        dockerProcess = None
        try:
            _t = subprocess.Popen(['mkdir', 'temp'],
                                  cwd=Config_Dict['compilerPath'])
            _t.wait(10)
            _t = subprocess.Popen(['cp', '-r', userCompilerPath, '/*', 'temp/'], cwd=Config_Dict['compilerPath'])
            _t.wait(10)
            with open(Config_Dict['compilerPath'] + '/temp/Dockerfile', 'w') as f:
                f.write(
                    'FROM %s\nADD * /compiler/\nWORKDIR /compiler\nRUN bash /compiler/build.bash' % (
                            Config_Dict['dockerprefix'] + 'base'))
            dockerProcess = subprocess.Popen(['docker', 'build', '-t', imageName, '.'],
                                             cwd=os.path.join(Config_Dict['compilerPath'], 'temp'),
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            dockerProcess.wait(Config_Dict['GitTimeout'])
            if dockerProcess.returncode == 0:
                build_verdict = 'Success'
            stdout_str = dockerProcess.stdout.readlines()
            stdout_str = ''.join([i.decode() for i in stdout_str[:20]])
            stderr_str = dockerProcess.stderr.readlines()
            stderr_str = ''.join([i.decode() for i in stderr_str[:20]])
            build_result = '==git stdout==\n{}\n==git stderr==\n{}\n==stdout==\n{}\n==stderr==\n{}'.format(
                git_build_stdout, git_build_stderr, stdout_str, stderr_str)
        except subprocess.TimeoutExpired:
            build_verdict = 'Timeout'
            build_result = 'Build timeout'
            genLog(
                '(Judge-Build)  Built Timeout occurred. target:%s -> %s' % (config_dict['uuid'], config_dict['ident']))
            dockerProcess.terminate() if not dockerProcess is None else _t.terminate()
        except Exception as identifier:
            build_verdict = 'Runtime Error'
            build_result = 'Build Runtime Error, {}'.format(identifier)
            genLog(
                '(Judge-Build)  Built Runtime Error occurred. %s / target:%s -> %s' % (
                    identifier, config_dict['uuid'], config_dict['ident']))
        _t = subprocess.Popen(['rm', '-rf', 'temp'], cwd=Config_Dict['compilerPath'])
        genLog('(Judge-Build)  built finished. target:%s' % config_dict)
        gitCommitLog = fetchGitCommit(userCompilerPath, hashResultRemote[1])
        return build_verdict, hashResultRemote[1], base64.b64encode(gitCommitLog.encode()).decode(), base64.b64encode(
            build_result.encode()).decode(), imageName
    else:
        # matched and exist
        # verdict, GitHash, GitCommit, BuildMessage
        log = fetchGitCommit(userCompilerPath, hashResultRemote[1])
        return 'Success', hashResultRemote[1], base64.b64encode(log.encode()).decode(), base64.b64encode(
            'Recently built.'.encode()).decode(), imageName


def build_compiler_local_adapter(config_dict: dict):
    assert 'uuid' in config_dict.keys()
    assert 'repo' in config_dict.keys()
    userCompilerPath = Config_Dict['compilerPath'] + '/' + config_dict['uuid']
    git_build_stdout = ''
    git_build_stderr = ''
    genLog('[coreModule.py] Generating repo with path: {}'.format(userCompilerPath))
    if not os.path.exists(userCompilerPath):
        os.makedirs(userCompilerPath)
        try:
            genLog('[coreModule.py] Start cloning object.')
            process = subprocess.Popen(['git', 'clone', config_dict['repo'], '.'], cwd=userCompilerPath,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait(Config_Dict['GitTimeout'])
            git_build_stdout = process.stdout.readlines()
            git_build_stdout = ''.join([i.decode() for i in git_build_stdout])
            git_build_stderr = process.stderr.readlines()
            git_build_stderr = ''.join([i.decode() for i in git_build_stderr])
        except subprocess.TimeoutExpired as identifier:
            git_build_stderr = 'Git Timeout'
            genLog('[coreModule.py] Git Timeout')
            process.terminate()
            return 'Fail', 'N/A', base64.b64encode('N/A'.encode()).decode(), base64.b64encode(
                git_build_stderr.encode()).decode(), ''
        except Exception as identifier:
            git_build_stderr = 'GitRuntime Error: {}'.format(identifier)
            genLog('[coreModule.py] {}'.format(git_build_stderr))
            return 'Fail', 'N/A', base64.b64encode('N/A'.encode()).decode(), base64.b64encode(
                git_build_stderr.encode()).decode(), ''
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
    gitCommitLog = fetchGitCommit(userCompilerPath, hashResultRemote[1])

    process = None
    try:
        process = subprocess.Popen(["bash", 'build.bash'], cwd=userCompilerPath,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        process.wait(90)
        stdout_result = process.stdout.readlines()
        stderr_result = process.stderr.readlines()
        stdout_result_str = ''.join([i.decode() for i in stdout_result])
        stderr_result_str = ''.join([i.decode() for i in stderr_result])
        log = '==git stdout==\n{}\n==git stderr==\n{}\n==stdout==\n{}\n==stderr==\n{}'.format(
            git_build_stdout, git_build_stderr, stdout_result_str, stderr_result_str)

        if process.returncode == 0:
            return 'Success', hashResultRemote[1], base64.b64encode(gitCommitLog.encode()).decode(), base64.b64encode(
                log.encode()).decode(), 'local'
        else:
            return 'Fail', hashResultRemote[1], base64.b64encode(gitCommitLog.encode()).decode(), base64.b64encode(
                log.encode()).decode(), 'local'
    except subprocess.TimeoutExpired as identifier:
        try:
            process.kill()
        except Exception as identifier:
            pass
        pass
        return 'Timeout', hashResultRemote[1], base64.b64encode(gitCommitLog.encode()).decode(), base64.b64encode(
            'build time out'.encode()).decode(), 'local'
    except Exception as identifier:
        return 'Runtime Error', hashResultRemote[1], base64.b64encode(gitCommitLog.encode()).decode(), base64.b64encode(
            'build runtime error'.encode()).decode(), 'local'
