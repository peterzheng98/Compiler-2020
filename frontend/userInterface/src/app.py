from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask import Flask, render_template
from flask_login import current_user, login_required

app = Flask(__name__)
Bootstrap(app)
nav = Nav()
# Should be closed if it is deployed
app.debug = True


@app.route('/')
def index():
    return render_template('index.html', webconfig={'title': 'Compiler 2020'}, current_user=1)

@app.route('/about')
def about():
    return 'This is the ABOUT page'

@app.route('/products/<product>')
def products(product):
    return 'product: ' + str(product)
if __name__ == '__main__':
    app.run('127.0.0.1', 5000)