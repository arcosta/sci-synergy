"""
Created on 07/03/2016

@author: aurelio
"""

import json
from flask import render_template, request, session, redirect, url_for

from scisynergy_flask import app
from .db import findArea
from .models import Researcher, GraphInfo
from flask import jsonify
from scisynergy_flask.models import Publication, Institution


@app.before_first_request
def initResearcher():
    r = Researcher()


@app.route('/')
@app.route('/index')
def index():
    idx = request.args.get('id')
    name = ''
    if idx is not None:
        name = Researcher().find(idx)
        if name != '':
            session['username'] = name
    try:
        gi = GraphInfo()
    except Exception as err:
        app.error_message = err
        return redirect(url_for('maintenance'))
    
    return render_template('home.html', name = name, graph_info = [gi.nodeCount(), gi.relCount()])


@app.route('/pubgraph', methods=['POST', 'GET'])
def showgraph():
    # TODO: Pegar as instituicoes para aplicar os filtros
    inst = {i: i.upper() for i in Institution().getInstitutionsName()}
    
    inst['all'] = 'All'
    selected = 'unb'
    if request.method == 'POST':
        selected = request.form['institution']
        
    return render_template('graphview.html', institutions=inst, selected=selected)


@app.route('/api.json')
def graphapi():
    instFilter = request.args.get('inst')
    return jsonify( Publication().relationCoauthoring(instFilter) )


@app.route('/iteraction.json')
def iteraction():
    return jsonify(Institution().institutionInteraction())


@app.route('/recommending', methods=['POST', 'GET'])
def recommending():
    if request.method == 'POST':
        name = request.form['name']
        r = Researcher().findByName(name)
        
        return render_template('recommending.html', recos=r)
    else:
        return render_template('recommending.html', recos=None)


@app.route('/acmtree')
def acmtree():
    return render_template('acmtree.html')


@app.route('/profile/<user_id>')
def show_profile(user_id):
    if not user_id or int(user_id) < 0:
        return 'Invalid user id ', 404
    
    r = Researcher().find(user_id)
    if r is None:
        return "User not found", 500
    return render_template('profile.html', user=r)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        queryterm = request.form['searchkey']
        hits = []
        
        for key in Researcher.indexOfNames.keys():
            for query_token in queryterm.split():
                if key == Researcher.tokenSanitize(query_token):
                    hits.append(set(Researcher.indexOfNames[key]))        
                 
        authors = list()
        if len(hits) == 0:
            return render_template("search.html", action='result', result=None, queryTerm=queryterm)
        else:            
            intersection = set.intersection(*hits)
        
            for i in intersection:
                author = Researcher().find(i)
                if author is not None:
                    authors.append(author)
        
        return render_template("search.html", action='result', result=authors)
    else:
        return render_template('search.html', action='query')


@app.route('/chord', methods=["GET"])
def chod():
    return render_template("chord.html")


@app.route('/autocomplete', methods=["GET"])
def autocomplete():
        partial = request.args.get('partial')
        
        area = findArea(partial)
        
        return json.dumps(area)


@app.errorhandler(404)
def page_not_found(error):
    return "A pagina solicitada nao esta disponivel",404


@app.route('/maintenance')
def maintenance():
    try:
        return render_template('maintenance.html', error_message = app.error_message)
    except AttributeError:
        return render_template('maintenance.html')
