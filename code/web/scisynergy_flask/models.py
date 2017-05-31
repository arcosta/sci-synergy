#-*- coding: latin-1 -*-
'''
Created on 20/04/2016

@author: aurelio
'''
#-*-coding: latin-1 -*-

from py2neo import Graph
import os
import sys
from .db import get_db

graph = ''

if os.environ.get('OPENSHIFT_PYTHON_IP') is not None:
    graph = Graph("http://datagraph-academicmetrics.rhcloud.com:80/db/data")
else:
    print('Using localhost database')
    graph = Graph()

#FIXME: Dont do this at home
def fix_code(_str, code):
    if sys.version_info > (2,9):
        return _str
    else:
        return unicode(_str, code)

class QuizReport(object):
    def __init__(self):
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT idusuario, idquestao, conteudo FROM resposta")
        
        answers = list()
        for rs in cur.fetchall():
            print(rs)
            answers.append(rs)
        self.answers = answers
        
    def getAnswersByAuthorId(self, idx):
        if not idx:
            return None
        
    def generateSummary(self):
        q1 = {}
        q2 = {}
        q3 = {}
        q4 = {}
        q5 = {}
        q6 = {}
        q7 = {}
        q8 = {}
        
        for a in self.answers:
            if a[1] == 'ps1':
                if q1.get(a[2]) is None:
                    q1[a[2]] = 1
                else:
                    q1[a[2]] += 1
            #q1        
            elif a[1] == 'ps1text1':
                if a[2] is not None and len(a[2]) > 2:
                    if q1.get('reason') is None:
                        q1['reason'] = [a[2]]
                    else:
                        q1['reason'].append(a[2])
            elif a[1] == 'ps1text2':
                if a[2] is not None and len(a[2]) > 2:
                    if q1.get('sugest') is None:
                        q1['sugest'] = [a[2]]
                    else:
                        q1['sugest'].append(a[2])
            #q2
            elif a[1].startswith('ps2') and len(a[2]) > 2:
                if q2.get('areas') is None:
                    q2['areas'] = [fix_code(a[2], 'utf-8')]
                else:
                    q2['areas'].append(fix_code(a[2], 'utf-8'))
            #q3
            elif a[1].startswith('ps3') and len(a[2]) > 2:
                if q3.get(a[1]) is None:
                    if a[1] == 'ps3text1':
                        q3[a[1]] = [int(a[2])]
                    else:
                        q3[a[1]] = [fix_code(a[2], 'latin-1')]
                else:
                    if a[1] == 'ps3text1':
                        q3[a[1]].append(int(a[2]))
                    else:
                        q3[a[1]].append(fix_code(a[2], 'latin-1'))
            #q4
            elif a[1] == 'ps4text' and len(a[2]) > 2:
                if q4.get(a[1]) is None:
                    q4[a[1]] = [fix_code(a[2], 'latin-1')]
                else:
                    q4[a[1]].append(fix_code(a[2], 'latin-1'))
            
            #q5
            elif a[1].startswith('ps5') and len(a[2]) > 2:
                # as categorias customizadas começam no 11
                if q5.get(a[1]) is None:
                    q5[a[1]] = [int(a[2])]
                else:
                    # Armazena o valor medio
                    #q5[a[1]] 
                    q5[a[1]].append(int(a[2]))
            
            #q6
            elif a[1].startswith('ps6') and len(a[2]) > 2:
                # As areas começam em 11
                if q6.get(a[1]) is None:
                    q6[a[1]] = [a[2]]
                else:
                    q6[a[1]].extend(a[2])
            
            #q7
            elif a[1].startswith('ps7r'):
                if q7.get(a[2]) is None:
                    q7[a[2]] = 1
                else:
                    q7[a[2]] += 1
            elif a[1].startswith('ps7text') and len(a[2]) > 2:
                if q7.get('comments') is None:
                    q7['comments'] = [fix_code(a[2], 'utf-8')]
                else:
                    q7['comments'].append(fix_code(a[2], 'utf-8'))
            #q8
            elif a[1] == 'ps8text1' and len(a[2]) > 2:
                if q8.get('comments') is None:
                    q8['comments'] = [fix_code(a[2], 'utf-8')]
                else:
                    q8['comments'].append(fix_code(a[2], 'latin-1'))
        if q7.get('yes') is not None and q7.get('no') is not None:
            q7['avg'] = q7.get('yes') / (q7.get('yes') + q7.get('no'))
        else:
            q7['avg'] = 0     
        return {'q1':q1, 'q2':q2, 'q3':q3, 'q4':q4, 'q5':q5, 'q6':q6, 'q7':q7, 'q8':q8}
             
    
    def countAnswers(self):
        db = get_db()
        c = db.cursor()
        c.execute("SELECT count(distinct idusuario) FROM resposta")
    
        return c.fetchone()[0]
    
    def getAnswers(self):     
        
        #TODO: Process the answers before send to view
        return self.answers
     
class Researcher(object):
    index_initialized = False
    indexOfNames = None
    
    def __init__(self):
        self.publications = list()
        if not Researcher.index_initialized:
            Researcher.indexOfNames = Researcher.initNamesIndex()
        
    
    @staticmethod
    def tokenSanitize(token):
        translationTable = None
        if sys.version_info < (2,9):
            import string 
            translationTable = string.maketrans("çàáâãèéêíóôõúñ", "caaaaeeeioooun")
            return token.lower().encode('latin-1').translate(translationTable)
        else:
            translationTable = str.maketrans("çàáâãèéêíóôõúñ", "caaaaeeeioooun", ": '`{}[])(@?!_-/")
            return token.lower().translate(translationTable)
    
        

    @staticmethod
    def initNamesIndex():
        invertedIndex = {}
        
        # Build index
        for author in graph.find("Author"):
            name = author['name']
            authorid = author['authorid']
            
            #TODO: Remove stopwords
            for token in name.split():
                if len(token) < 3:
                    # Do not include short tokens
                    continue
                token = Researcher.tokenSanitize(token)
                if invertedIndex.get(token) is None:
                    invertedIndex[token] = [authorid]
                else:
                    invertedIndex[token].append(authorid)
                
        print("Index created with %i terms" %len(invertedIndex))
        Researcher.index_initialized = True
        return invertedIndex

        
    def updateInfos(self, remoteNode):
        self.name = remoteNode['name']
        self.bagofareas = remoteNode['bagofareas']
        self.lattesurl = remoteNode['lattesurl']
        self.userid = remoteNode['authorid']
        self.recomendation = list()
        for rec in remoteNode.match_outgoing("RECOMMENDATION"):
            recArea = rec.properties.get('area')
            
            recStr = rec.end_node['name']
            institution = ''            
            if [x for x in self.recomendation if x.find(recStr) >= 0]:
                continue
            for assoc in rec.end_node.match_outgoing("ASSOCIATED TO"):
                institution = assoc.end_node['name']
            if rec.end_node['PQ'] is not None:
                recStr += " (" + rec.end_node['PQ'] + ")"
            if institution != '':
                recStr += ' - <b>'+ institution.upper()+'</b>'
            
            if recArea is not None:
                recStr += " - Area: " + recArea
                
            self.recomendation.append(recStr)
        
    def find(self, idx = 0):
        if idx is None or idx == 0:
            return None
        retVal = graph.find_one("Author", 'authorid', int(idx))        
        
        if retVal is not None:
            self.updateInfos(retVal)            
            
        return self
    
    def findByName(self, name=''):
        if not name or name == '':
            return None
        
        retVal = graph.find_one("Author", 'name', name)
        if retVal is not None:
            self.updateInfos(retVal)             
        
        return self
    
class Publication(object):
    def __init__(self):
        pass
    def relationCoauthoring(self, institution=None):
        queryRelations = '''MATCH 
    (a:Author)-[r1:AUTHORING]-(p:Publication)-[r2:AUTHORING]-(b:Author) 
WHERE 
    p.type='article' AND a <> b 
WITH
    p,a,b
OPTIONAL MATCH 
    (a)-[rv:`ASSOCIATED TO`]-(i:Institution)
RETURN a, b, count(p), i'''
        
        if institution is not None and institution != 'all':
            queryRelations = '''MATCH 
    (i:Institution {name: "%s"})-[r1:`ASSOCIATED TO`]-(a:Author)-[r2:AUTHORING]-(p:Publication)-[r3:AUTHORING]-(b:Author) 
WHERE 
    p.type='article' 
RETURN a, b, count(p), i''' % institution
            
        
        relations = graph.cypher.execute(queryRelations)
        links = list()
        if relations.__len__() < 10:
            raise Exception("Few nodes")
        for r in relations:
            links.append({"source":r[0]["name"], 
                          "target":r[1]["name"], 
                          "size":6,
                          "rel_count":r[2],
                          "institution": r[3]['color'] if r[3] is not None else 'yellow'
                        })
        print("Modelo criado com %i arestas" % len(links))    
        return dict(children=links)
        
    def relationAuthorPublication(self):
        queryRelations = "MATCH (a:Author)<-[r:AUTHORING]->(p:Publication) WHERE p.type='article' RETURN a,p"
        relations = graph.cypher.execute(queryRelations)
            
        links = list()
        if relations.__len__() < 10:
            raise Exception("Few nodes")
        for r in relations:
            links.append({"source":r[0]["name"], 
                                    "target":r[1]["key"], 
                                    "size":6}
            )
            
        return dict(children=links)
    
class Institution(object):
    def __init__(self):
        pass
    def getInstitutionsName(self):
        
        return [inst['name'] for inst in graph.find("Institution")]
class GraphInfo(object):
    def __init__(self):
        pass
    def nodeCount(self):
        return graph.cypher.execute("MATCH (n) RETURN count(n) AS nodes")[0]['nodes']
    def relCount(self):
        return graph.cypher.execute("MATCH ()-[r]-() RETURN count(r) AS rels")[0]['rels']
    