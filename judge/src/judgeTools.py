from dockerTools import C, getImage
from ConfigDeploy import Config_Dict
import docker
import requests
import time
import os
import base64
import subprocess


def judgeSemantic(taskDict: dict):
    """
    Judge the source code and return the result.
    :param taskDict: TaskInformation
    :return: A tuple(int, str). tuple[0] indicating the result. 0/1 for Accepted/Wrong Answer.   2 for Runtime Error. tuple[1] for message. 3 for Timeout
    """
    # Dispatch the data
    # This is safe since checkSemanticVaildity is checked before
    uuid, imageName, sourceCode, assertion = taskDict['uuid'], taskDict['imagename'], taskDict['inputSourceCode'], \
                                             taskDict['assertion']
    timeLimit, memoryLimit = taskDict['timeLimit'], taskDict['memoryLimit']
    sourceCode = base64.b64decode(sourceCode.encode()).decode()
    container = None
    try:
        # Find the image and try to start the image
        start_time = time.time()
        path_prefix = os.path.join(Config_Dict['compilerPath'], 'judgeData')
        open(os.path.join(path_prefix, 'judgeSemantic.bash'), 'w').write(
            'cat /judgeData/testdata.txt | bash /compiler/semantic.bash')
        open(os.path.join(path_prefix, 'testdata.txt'), 'w').write(sourceCode)
        container = C.containers.run(
            image=imageName,
            command='bash /judgeData/judgeSemantic.bash',
            detach=True, stdout=True, stderr=True,
            mem_limit='{}m'.format(memoryLimit),
            volumes={
                os.path.join(Config_Dict['compilerPath'], 'judgeData'): {
                    'bind': '/judgeData', 'mode': 'ro'
                }
            }, cpu_period=100000, cpu_quota=400000, network_mode='none'
        )
        container_running_result = container.wait(timeout=timeLimit)
        time_interval = time.time() - start_time
        containerExitCode, stdout, stderr = container_running_result['StatusCode'], \
                                            container.logs(stdout=True, stderr=False), \
                                            container.logs(stdout=False, stderr=True)
        assertion = True if assertion == '1' else False
        if assertion == (containerExitCode == 0):
            return_mess = ('==Verdict==\nAccepted\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                containerExitCode, stdout[0:Config_Dict['MaxlogSize']].decode(),
                stderr[0:Config_Dict['MaxlogSize']].decode()
            )).encode()
            return '0', base64.b64encode(return_mess).decode(), time_interval
        else:
            return_mess = ('==Verdict==\nWrong Answer\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                containerExitCode, stdout[0:Config_Dict['MaxlogSize']].decode(),
                stderr[0:Config_Dict['MaxlogSize']].decode()
            )).encode()
            return '1', base64.b64encode(return_mess).decode(), time_interval

    except docker.errors.ImageNotFound as identifier:
        return '2', 'Docker Image not found, {}'.format(identifier), -1
    except requests.exceptions.ReadTimeout as identifier:
        # Run time out, require kill the container
        containerExitCode, stdout, stderr = container_running_result['StatusCode'], \
                                            container.log(stdout=True, stderr=False), \
                                            container.log(stdout=False, stderr=True)
        try:
            container.kill()
        except Exception as identifier:
            pass
        return_mess = ('==Verdict==\nTimeout\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
            containerExitCode, stdout[0:Config_Dict['MaxlogSize']].decode(),
            stderr[0:Config_Dict['MaxlogSize']].decode()
        )).encode()
        return '3', base64.b64encode(return_mess).decode(), timeLimit
    except Exception as identifier:
        return '2', 'Unknown error occurred, {}'.format(identifier), timeLimit


def judgeCodeGen(taskDict: dict):
    """
    Judge the source code and return the result in tuples
    :param taskDict: TaskInformation
    :return: A tuple(int, str). tuple[0] indicating the result. 0/1 for Accepted/Wrong Answer.
    2 for Runtime Error. tuple[1] for message. 3 for Timeout
    """
    # Here wait for matching
    inputSrcCode = base64.b64decode(taskDict['inputSourceCode'].encode()).decode()
    inputContent = base64.b64decode(taskDict['inputContent'].encode()).decode()
    outputCode = base64.b64decode(taskDict['outputCode'].encode()).decode()
    outputContent = base64.b64decode(taskDict['outputContent'].encode()).decode()
    timeLimit = taskDict['timeLimit']
    memoryLimit = taskDict['memoryLimit']
    uuid, imageName = taskDict['uuid'], taskDict['imagename']
    userCompilerPath = Config_Dict['compilerPath'] + '/' + uuid
    textMessage = 'Start Judge:\n--> Stage 1: Compile the program\n{}\n'.format('-' * 30)
    user_generated_output = ''
    # Stage 1: Compile the program.
    try:
        # Find the image and try to start the image
        start_time = time.time()
        path_prefix = os.path.join(Config_Dict['compilerPath'], 'judgeData')
        open(os.path.join(path_prefix, 'judgeCodegen.bash'), 'w').write(
            'cat {} | bash {}/codegen.bash'.format(
                os.path.join(os.path.join(Config_Dict['compilerPath'], 'judgeData'), 'testdata.txt'), userCompilerPath))
        open(os.path.join(path_prefix, 'testdata.txt'), 'w').write(inputSrcCode)
        process = subprocess.Popen(['bash', 'judgeCodegen.bash'], cwd=path_prefix, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        try:
            process.wait(15)
            time_interval = time.time() - start_time
            stdout_result = process.stdout.readlines()
            stderr_result = process.stderr.readlines()
            stdout_result_str = ''.join([i.decode() for i in stdout_result])
            stderr_result_str = ''.join([i.decode() for i in stderr_result])

            if process.returncode == 0:
                textMessage = textMessage + '==Compile Stderr==\n{}\n{}'.format(
                    stderr_result_str[0:Config_Dict['MaxlogSize']], '-' * 30)
                user_generated_output = stdout_result_str
            else:
                textMessage = textMessage + '==Compile Stderr==\n{}\n{}'.format(
                    stderr_result_str[0:Config_Dict['MaxlogSize']], 'Compiling returned non-zero value')
                return '1', base64.b64encode(textMessage).decode(), time_interval, timeLimit
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass
            pass
            textMessage = textMessage + '==Compile Stderr==\n{}\n{}'.format('', 'Compiling Time out')
            return '1', base64.b64encode(textMessage).decode(), timeLimit, timeLimit
        except Exception as identifier:
            textMessage = textMessage + '==Compile Stderr==\n{}\n{}'.format('', 'Compiler Crash')
            return '1', base64.b64encode(textMessage).decode(), timeLimit, timeLimit
    except Exception as identifier:
        return '1', base64.b64encode(
            textMessage + 'Unknown error occurred, {}'.format(identifier)).decode(), timeLimit, timeLimit


    return '2', 'Under development', -1, -1


def judgeSemantic_local_adapter(taskDict: dict):
    uuid, imageName, sourceCode, assertion = taskDict['uuid'], taskDict['imagename'], taskDict['inputSourceCode'], \
                                             taskDict['assertion']
    timeLimit, memoryLimit = taskDict['timeLimit'], taskDict['memoryLimit']
    sourceCode = base64.b64decode(sourceCode.encode()).decode()
    userCompilerPath = Config_Dict['compilerPath'] + '/' + uuid
    process = None
    try:
        # Find the image and try to start the image
        start_time = time.time()
        path_prefix = os.path.join(Config_Dict['compilerPath'], 'judgeData')
        open(os.path.join(path_prefix, 'judgeSemantic.bash'), 'w').write(
            'cat {} | bash {}/semantic.bash'.format(
                os.path.join(os.path.join(Config_Dict['compilerPath'], 'judgeData'), 'testdata.txt'), userCompilerPath))
        open(os.path.join(path_prefix, 'testdata.txt'), 'w').write(sourceCode)
        process = subprocess.Popen(['bash', 'judgeSemantic.bash'], cwd=path_prefix, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        try:
            process.wait(timeLimit)
            time_interval = time.time() - start_time
            stdout_result = process.stdout.readlines()
            stderr_result = process.stderr.readlines()
            stdout_result_str = ''.join([i.decode() for i in stdout_result])
            stderr_result_str = ''.join([i.decode() for i in stderr_result])
            expectedResult = True if assertion == '1' else False

            if process.returncode == 0 and expectedResult:
                return_mess = ('==Verdict==\nAccepted\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                    process.returncode, stdout_result_str[0:Config_Dict['MaxlogSize']],
                    stderr_result_str[0:Config_Dict['MaxlogSize']]
                )).encode()
                return '0', base64.b64encode(return_mess).decode(), time_interval

            elif process.returncode != 0 and (not expectedResult):
                return_mess = ('==Verdict==\nAccepted\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                    process.returncode, stdout_result_str[0:Config_Dict['MaxlogSize']],
                    stderr_result_str[0:Config_Dict['MaxlogSize']]
                )).encode()
                return '0', base64.b64encode(return_mess).decode(), time_interval
            else:
                return_mess = ('==Verdict==\nFailed\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                    process.returncode, stdout_result_str[0:Config_Dict['MaxlogSize']],
                    stderr_result_str[0:Config_Dict['MaxlogSize']]
                )).encode()
                return '1', base64.b64encode(return_mess).decode(), time_interval
            pass
        except subprocess.TimeoutExpired:

            try:
                process.kill()
            except Exception:
                pass
            pass
            return_mess = ('==Verdict==\nTimeout\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                process.returncode, '', ''
            )).encode()
            return '1', base64.b64encode(return_mess).decode(), timeLimit
        except Exception as identifier:
            return_mess = ('==Verdict==\nRuntime Error\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                process.returncode, '', ''
            )).encode()
            return '1', base64.b64encode(return_mess).decode(), -1
    except Exception as identifier:
        return '2', 'Unknown error occurred, {}'.format(identifier), timeLimit
