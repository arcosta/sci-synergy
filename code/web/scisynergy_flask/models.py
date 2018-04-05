'''
Created on 20/04/2016

@author: aurelio
'''
#-*-coding: UTF-8 -*-

from py2neo import Graph
import os
import sys
from functools import lru_cache

graph = ''

if os.environ.get('GAE_DEPLOYMENT_ID', 'bar') == 'bar':
    graph = Graph(hostname='localhost', user='neo4j', password='scisynergy', bolt=True)
else:
    print('Using foreign database')
    try:
        graph = Graph(host='10.158.0.2', user='neo4j', password='scisynergy', bolt=True)
        #graph = Graph("http://hobby-bidcndeimgoagbkedjkhegkl.dbs.graphenedb.com:24789/db/data", user='openshiftuser', password='b.f7S3vbVb1bFO.wyLRsA6wEhkOjLUz')
        #graph = Graph(host=os.getenv("DATAGRAPH_SERVICE_HOST","datagraph.sci-synergy.svc"), user='neo4j', password='neo4j', bolt=True)
    except Exception as err:
        print("Graph connection error: ", err)
        graph = ''

#FIXME: Dont do this at home
def fix_code(_str, code):
    if sys.version_info > (2,9):
        return _str
    else:
        return unicode(_str, code)

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
            translationTable = string.maketrans("çàáâãéèêíóòöõüñ", "caaaaeeeiooooun")
            return token.lower().encode('utf-8').translate(translationTable)
        else:
            translationTable = str.maketrans("çàáâãéèêíóòöõüñ", "caaaaeeeiooooun", ":'`{}[])(@?!_-/")
            return token.lower().translate(translationTable)

    @staticmethod
    def initNamesIndex():
        invertedIndex = {}        
        if graph == '':
            return None
        for author in graph.find("Author"):
            name = author['name']
            authorid = id(author)
            if author.get('userid', 'x') == 'x':                
                author['userid'] = int(authorid)
                graph.push(author)
            else:
                authorid = author.get('userid')
            
            
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
        '''
        @desc Update user informations fetched from database
        '''
        self.name = remoteNode['name']
        self.bagofareas = remoteNode['bagofareas']
        self.lattesurl = remoteNode['lattesurl']
        self.userid = remoteNode['userid']
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
        if graph == '':
            return None
        retVal = None
        for author in graph.find("Author"):
            if author['userid'] == int(idx):
                retVal = author
                
        if retVal is not None:
            self.updateInfos(retVal)            
            
        return self
    
    def findByName(self, name):
        if not name or name == '':
            return None
        if graph == '':
            return None
        retVal = graph.find_one('Author', 'name', name)
        if retVal is not None:
            self.updateInfos(retVal)             
        
        return self
    
class Publication(object):
    def __init__(self):
        pass
    def colorcode(self, inst):
        colormap = {'ufrn':'blue',
                    'unb':  'green',
                    'ufam': 'gray',
                    'usp': 'red',
                    'ufmg': 'black'
                    }
        return colormap.get(inst, 'yellow')
        
    def relationCoauthoring(self, institution=None):
        queryRelations = '''MATCH 
    (a:Author)-[r1:AUTHORING]-(p:Publication)-[r2:AUTHORING]-(b:Author) 
WHERE 
    p.type='article' AND a <> b 
WITH
    p,a,b
OPTIONAL MATCH 
    (a)-[rv:`ASSOCIATED TO`]-(i:Institution)
RETURN a, b, count(p) as c, i'''
        
        if institution is not None and institution != 'all':
            queryRelations = '''MATCH 
    (i:Institution {name: "%s"})-[r1:`ASSOCIATED TO`]-(a:Author)-[r2:AUTHORING]-(p:Publication)-[r3:AUTHORING]-(b:Author) 
WHERE 
    p.type='article' 
RETURN a, b, count(p) as c, i''' % institution
                    
        relations = graph.run(queryRelations).data()
        links = list()
        if len(relations) < 10:
            raise Exception("Few nodes")
        for r in relations:
            links.append({"source":r['a']["name"], 
                          "target":r['b']["name"], 
                          "size":6,
                          "rel_count":r['c'],
                          "institution": self.colorcode(r['i']['name']) if r['i'] is not None else 'yellow'
                        })
        print("Modelo criado com %i arestas" % len(links))    
        return dict(children=links)
        
    def relationAuthorPublication(self):
        queryRelations = "MATCH (a:Author)<-[r:AUTHORING]->(p:Publication) WHERE p.type='article' RETURN a,p"
        relations = graph.run(queryRelations)
            
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
    def institutionInteraction(self):
        query = '''MATCH path=(i1:Institution)-[]-(a1:Author)-[]-(p:Publication)-[]-(a2:Author)-[]-(i2:Institution)
                WHERE id(i1) > id(i2)
                RETURN i1.name,i2.name, count(p)
                '''
        interaction = graph.run(query)
        interlist = list()
        for i in interaction:
            interlist.append({"source":i[0], "target":i[1], "rel_count":i[2]})
        return dict(result=interlist)

class GraphInfo(object):
    def __init__(self):
        if type(graph) is str:
            raise RuntimeError("Graph not connected")
    def nodeCount(self):
        return graph.run("MATCH (n) RETURN count(n) AS nodes").data()[0]['nodes']
        
    def relCount(self):
        return graph.run("MATCH ()-[r]-() RETURN count(r) AS rels").data()[0]['rels']
        
    def avgDegree(self):
        numNodes = self.nodeCount()
        numRels = self.relCount()
        return numRels / numNodes
        
    def betweenness(self):
        pass
        
    def closeness(self):
        pass
        
    def diameter(self):
        pass
        
    @lru_cache(maxsize=1024)    
    def distance(self, x, y):
        pass
    