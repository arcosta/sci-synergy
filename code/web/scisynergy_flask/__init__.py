'''
Created on 07/03/2016

@author: aurelio
'''

from flask import Flask, g
from contextlib import closing
import json, re, os
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = '#@$dqeqwe12e11w1cc'


@app.before_first_request
def extrat_acm_area_names():    
    json_raw = open(os.path.join('scisynergy_flask',os.path.join('static', 'acmtree.json')), 'r').read()
    prog = re.compile(r'"name": "([^"]+)"')
    areasName = prog.findall(json_raw, re.IGNORECASE)
    setattr(app, 'acmareas', areasName)

import scisynergy_flask.views     

if __name__ == '__main__':
    pass