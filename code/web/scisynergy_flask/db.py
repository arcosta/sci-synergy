#-*-coding: latin-1 -*-

from flask import g
from scicoll_flask import app, connect_db



#def connect_db():
#    conn = psycopg2.connect(app.config.get('PGDB_URI'))
#    
#    return conn
    
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
    return db


##########################
def get_username(idx):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT nome FROM usuario WHERE id=%s;", idx)
    name = c.fetchone()[0]
    
    return name
def insert_answer(user, field, answer):
    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO resposta(idusuario, idquestao, conteudo) VALUES(%s,%s,%s);", (user, field, answer))
    db.commit()

def getAnswers():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM resposta")
    retVal = list()
    for i in c.fetchall():
        retVal.append(i)
        
    return retVal
    
##########################

def findArea(partial):
    areas_list = getattr(app, 'acmareas')
    retList = list()
    for area in areas_list:
        if area.find(partial) > 0:
            retList.append(area)
        
    return retList