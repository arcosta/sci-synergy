'''
Created on 07/03/2016

@author: aurelio
'''

from scisynergy_flask import app
import os

if __name__ == '__main__':
    try:
        app.run(debug=True, host=os.environ['OPENSHIFT_PYTHON_IP'], port=int(os.environ['OPENSHIFT_PYTHON_PORT']))
    except KeyError as err:
        print("OPENSHIFT env not available, local running")
        app.run(debug=False, host="0.0.0.0", port=8080)