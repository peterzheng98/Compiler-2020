from dockerTools import C, getImage
from ConfigDeploy import Config_Dict
import docker
import requests
import time
import os
import base64


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
    container = None
    try:
        # Find the image and try to start the image
        start_time = time.time()
        path_prefix = os.path.join(Config_Dict['compilerPath'], 'judgeData')
        open(os.path.join(path_prefix, 'judgeSemantic.bash'), 'w').write(
            'cat /judgeData/testdata.txt | bash /compiler/semantic.sh')
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
            }, cpu_period=100000, cpu_quota=100000, network_mode='none'
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
    return '2', 'Under development', -1, -1
