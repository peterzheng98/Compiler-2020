from dockerTools import C, getImage
from ConfigDeploy import Config_Dict
import docker
import requests


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
        container = C.containers.run(
            image=imageName,
            command='bash /testrun/judgeSemantic.bash',
            detach=True, stdout=True, stderr=True,
            mem_limit=memoryLimit
        )
        container_running_result = container.wait(timeout=timeLimit)
        containerExitCode, stdout, stderr = container_running_result['StatusCode'], \
                                            container.log(stdout=True, stderr=False), \
                                            container.log(stdout=False, stderr=True)
        if assertion == (containerExitCode == 0):
            return '0', '==Verdict==\nAccepted\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                containerExitCode,
                stdout[0:Config_Dict['MaxlogSize']],
                stderr[0:Config_Dict['MaxlogSize']])
        else:
            return '1', '==Verdict==\nWrong Answer\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
                containerExitCode,
                stdout[0:Config_Dict['MaxlogSize']],
                stderr[0:Config_Dict['MaxlogSize']])
    except docker.errors.ImageNotFound as identifier:
        return '2', 'Docker Image not found, {}'.format(identifier)
    except requests.exceptions.ReadTimeout as identifier:
        # Run time out, require kill the container
        containerExitCode, stdout, stderr = container_running_result['StatusCode'], \
                                            container.log(stdout=True, stderr=False), \
                                            container.log(stdout=False, stderr=True)
        try:
            container.kill()
        except Exception as identifier:
            pass
        return '3', '==Verdict==\nTimeout\n==Exit Code==\n{}\n==Stdout==\n{}\n==Stderr==\n{}\n'.format(
            containerExitCode,
            stdout[0:Config_Dict['MaxlogSize']],
            stderr[0:Config_Dict['MaxlogSize']])
    except Exception as identifier:
        return '2', 'Unknown error occurred, {}'.format(identifier)


def judgeCodeGen(taskDict: dict):
    """
    Judge the source code and return the result in tuples
    :param taskDict: TaskInformation
    :return: A tuple(int, str). tuple[0] indicating the result. 0/1 for Accepted/Wrong Answer.
    2 for Runtime Error. tuple[1] for message. 3 for Timeout
    """
    # Here wait for Yunwei Ren's simulator
    return '-1', 'Under development'
