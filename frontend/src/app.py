from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask import Flask, render_template
app = Flask(__name__)
Bootstrap(app)
nav = Nav()
# Should be closed if it is deployed
app.debug = True

def top_navigateBar():
    return Navbar(
    View('Compiler Online Judge', 'index'),
    
    Subgroup(
        'Productsddd',
        View('Wg240-Series', 'products', product='wg240'),
        View('Wg250-Series', 'products', product='wg250'),
        Separator(),
        Text('Discontinued Products'),
        View('Wg10X', 'products', product='wg10x'),
    ),
    Link('Tech Support', 'http://techsupport.invalid/widgits_inc'),
    View('About', 'about')
)


nav.register_element('top', top_navigateBar)


nav.init_app(app)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return 'This is the ABOUT page'

@app.route('/products/<product>')
def products(product):
    return 'product: ' + str(product)
if __name__ == '__main__':
    app.run('127.0.0.1', 5000)