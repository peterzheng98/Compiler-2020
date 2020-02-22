from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask import Flask, render_template
from flask_login import current_user, login_required
import subprocess

app = Flask(__name__)
Bootstrap(app)
nav = Nav()
# Should be closed if it is deployed
app.debug = True


def getGitHash(pathORurl: str):
    '''
    Input: path
    Returns: Tuple<int, str> -> int: 1 Success 2 Error
    '''
    gitcmd = 'git ls-remote %s | grep heads/master' % pathORurl
    version = []
    try:
        version = subprocess.check_output(gitcmd, shell=True, timeout=5).decode().strip().split('\t')
        if len(version[0]) != 40:
            return 2, 'Length error, received [%s] with raw [%s]' % (version[0], '\t'.join(version))
        return 1, version[0]
    except subprocess.TimeoutExpired as identifier:
        return 2, 'Git Timeout: %s' % identifier
    except Exception as identifier:
        return 2, 'Exception: %s' % identifier


@app.route('/')
def index():
    code, gitHash = getGitHash('https://github.com/peterzheng98/Compiler-2020-testcases')
    if code != 1:
        gitHash = 'Error: Unable to get the remote version now.'
    return render_template('index.html', webconfig={'title': 'Compiler 2020'}, current_user=1, githash=gitHash)

@app.route('/about')
def about():
    return 'This is the ABOUT page'

@app.route('/products/<product>')
def products(product):
    return 'product: ' + str(product)
if __name__ == '__main__':
    app.run('127.0.0.1', 5000)