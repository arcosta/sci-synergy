'''
Created on 07/03/2016

@author: aurelio
'''

from flask import Flask, g
from contextlib import closing
import psycopg2, json, re, os
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = '#@$dqeqwe12e11w1cc'

PGDB_URI = ""

if os.environ.get('OPENSHIFT_PYTHON_IP'):
    PGDB_URI = 'user=' + os.environ.get('OPENSHIFT_POSTGRESQL_DB_USERNAME')+ ' password=' + os.environ.get('OPENSHIFT_POSTGRESQL_DB_PASSWORD') + ' host='+os.environ.get('OPENSHIFT_POSTGRESQL_DB_HOST')
else:
    PGDB_URI = 'user=usuarioscicoll password=password host=localhost'
    

def connect_db():
    conn = psycopg2.connect(PGDB_URI)
    conn.set_client_encoding('utf8')
    return conn

def init_db():
    global PGDB_URI
    # Create database if necessary
    conn = psycopg2.connect(PGDB_URI + ' dbname=postgres')
    cur = conn.cursor()
    cur.execute('SELECT datname FROM pg_database')
    yetCreated = False
    for row in cur.fetchall():
        if row[0].find('scicoll') == 0:
            yetCreated = True
    
    if not yetCreated:
        conn.set_isolation_level(0)
        cur.execute('CREATE DATABASE scicoll')
        cur.commit()
        conn.close()
            
    PGDB_URI += ' dbname=scicoll'
    
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            
            db.cursor().execute(f.read())
        db.commit()
    

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.before_first_request
def extrat_acm_area_names():    
    json_raw = open(os.path.join('scicoll_flask',os.path.join('static', 'acmtree.json')), 'r').read()
    prog = re.compile(r'"name": "([^"]+)"')
    areasName = prog.findall(json_raw, re.IGNORECASE)
    
    setattr(app, 'acmareas', areasName)
    
    init_db()
    
    setattr(g, '_database', connect_db())
    
    

import scicoll_flask.views     

if __name__ == '__main__':
    pass