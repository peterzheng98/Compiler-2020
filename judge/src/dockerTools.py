import docker
C = docker.from_env()


def getImage(imageName):
    return C.images.get(imageName)


def existImage(imageName):
    try:
        C.images.get(imageName)
        return True
    except docker.errors.ImageNotFound as identifier:
        return False
    except Exception:
        return False


def makeContainer(dockerfilePath: str, imageName: str):
    try:
        # this may take very very long time
        print('Build Base Image, which will take a very long time')
        imagesbuilt_Tuple = C.images.build(path=dockerfilePath, tag=imageName)
        print('Build finished')
        return True, imagesbuilt_Tuple[1], imagesbuilt_Tuple[0]
    except Exception as identifier:
        return False, 'An error in executing makeContainer(%s, %s) in core.py. [%s]' % (
            dockerfilePath, imageName, identifier)
        pass


def cleanDocker():
    '''
    Clean all the existing docker. Except for the base docker.
    The dockerPrefix is set in ConfigDeploy.
    '''
    ImageLists = C.images.list()
    for image in ImageLists:
        C.images.remove(image=image.tags)
    pass