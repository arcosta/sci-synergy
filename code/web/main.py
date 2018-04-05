'''
Created on 07/03/2016

@author: aurelio
'''

from scisynergy_flask import app
import os

if __name__ == '__main__':
    if os.environ.get('GAE_DEPLOYMENT_ID', 'bar') == 'bar':
        print("Running at home")
        app.run(debug=True, host="0.0.0.0", port=8080)
    else:
        print("Running on GCP")
        app.run(debug=False, host="0.0.0.0", port=8080)