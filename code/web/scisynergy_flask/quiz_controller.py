"""
Created on 01/10/2018

@author: aurelio
"""

from flask import render_template, request, session, redirect, url_for

from scisynergy_flask import app
from .models import Researcher
from flask.helpers import make_response


def insert_answer(userid, idx, form):
    pass


@app.route('/questionario', methods=['GET', 'POST'])
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        for i in request.form.keys():
            # g.db.insert_answer(1, i, request.form[i])
            userid = request.cookies.get('userid')
            if userid is None:
                userid = 1
            insert_answer(userid, i, request.form[i])
        return render_template('thanks.html')
    else:
        userid = request.cookies.get('userid')
        if userid is not None:
            r = Researcher().find(userid)
            return render_template('quiz.html', user=r)
        else:
            return render_template('quiz.html')


@app.route('/startquiz')
def startquiz():
    idx = request.args.get('id')

    r = Researcher().find(idx)

    if r is not None:
        resp = make_response(render_template('index.html', name=r.name))
        resp.set_cookie('userid', str(r.userid))
        return resp
    else:
        return render_template('index.html', name=None)
