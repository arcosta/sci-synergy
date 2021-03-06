"""
Created on 20/04/2016

@author: aurelio
"""

from py2neo import Graph
from py2neo.matching import RelationshipMatch
import os
import sys
from functools import lru_cache

graph = ''


if os.environ.get('GAE_DEPLOYMENT_ID', 'bar') == 'bar':
    print('Using docker stack')
    try:
        graph = Graph(os.getenv('NEO4J_URI'), user='neo4j', password='scisynergy')
        
    except IOError as e:
        print("!! No database available !!")    
else:
    print('Using foreign database')
    try:
        graph = Graph(host='10.158.0.2', user='neo4j', password='scisynergy', bolt=True)
        
    except Exception as err:
        print("Graph connection error: ", err)
        graph = ''


def verify_database():
    if len(graph) == 0:
        raise Exception("Empty Graph")


class Researcher(object):
    index_initialized = False
    indexOfNames = None
    
    def __init__(self):
        self.publications = list()
        self.name = ''
        self.bagofareas = ''
        self.lattesurl = ''
        self.userid = ''
        self.recomendation = list()
        if not Researcher.index_initialized:
            Researcher.indexOfNames = Researcher.initNamesIndex()        
    
    @staticmethod
    def tokenSanitize(token):
        if sys.version_info < (2, 9):
            import string 
            translationTable = string.maketrans("çàáâãéèêíóòöõüñ", "caaaaeeeiooooun")
            return token.lower().encode('utf-8').translate(translationTable)
        else:
            translationTable = str.maketrans("çàáâãéèêíóòöõüñ", "caaaaeeeiooooun", ":'`{}[])(@?!_-/")
            return token.lower().translate(translationTable)

    @staticmethod
    def initNamesIndex():
        inverted_index = {}
        if graph == '':
            return None
        for author in graph.nodes.match("Author"):
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
                if inverted_index.get(token) is None:
                    inverted_index[token] = [authorid]
                else:
                    inverted_index[token].append(authorid)
                
        print("Index created with %i terms" % len(inverted_index))
        Researcher.index_initialized = True
        return inverted_index

    def updateInfos(self, remote):
        """
        @desc Update user informations fetched from database
        """
        self.name = remote['name']
        self.bagofareas = remote['bagofareas']
        self.lattesurl = remote['lattesurl']
        self.userid = remote['userid']
        self.recomendation = list()

        for rec in RelationshipMatch(graph, nodes=[remote], r_type="RECOMMENDATION"):
            rec_area = rec.get('area')
            
            rec_str = rec.end_node['name']
            institution = ''            
            if [x for x in self.recomendation if x.find(rec_str) >= 0]:
                continue
            for assoc in rec.end_node.match_outgoing("ASSOCIATED TO"):
                institution = assoc.end_node['name']
            if rec.end_node['PQ'] is not None:
                rec_str += " (" + rec.end_node['PQ'] + ")"
            if institution != '':
                rec_str += ' - <b>' + institution.upper() + '</b>'
            
            if rec_area is not None:
                rec_str += " - Area: " + rec_area
                
            self.recomendation.append(rec_str)

    def find(self, idx = 0):
        if idx is None or idx == 0:
            return None
        if graph == '':
            return None
        retval = None
        for author in graph.nodes.match("Author"):
            if author['userid'] == int(idx):
                retval = author
                
        if retval is not None:
            self.updateInfos(retval)
        return self
    
    def findByName(self, name):
        if not name or name == '':
            return None
        if graph == '':
            return None
        retVal = graph.nodes.match('Author', name=name).first()
        if retVal is not None:
            self.updateInfos(retVal)             
        
        return self


class Publication(object):
    def __init__(self):
        pass

    def find_by_author(author):
        publications = list()
        for rel in RelationshipMatch(graph, nodes=[author], r_type="AUTHORING"):
            (a,r,p) = rel.walk()
            publications.append(p)
        return publications

    @staticmethod
    def colorcode(inst):
        colormap = {'ufrn': 'blue',
                    'unb': 'green',
                    'ufam': 'gray',
                    'usp': 'red',
                    'ufmg': 'black'
                    }
        return colormap.get(inst, 'yellow')

    def relationCoauthoring(self, institution=None):
        query_relations = '''MATCH 
    (a:Author)-[r1:AUTHORING]-(p:Publication)-[r2:AUTHORING]-(b:Author) 
WHERE 
    p.type='article' AND a <> b 
WITH
    p,a,b
OPTIONAL MATCH 
    (a)-[rv:`ASSOCIATED TO`]-(i:Institution)
RETURN a, b, count(p) as c, i'''
        
        if institution is not None and institution != 'all':
            query_relations = '''MATCH 
    (i:Institution {name: "%s"})-[r1:`ASSOCIATED TO`]-(a:Author)-[r2:AUTHORING]-(p:Publication)-[r3:AUTHORING]-(b:Author) 
WHERE 
    p.type='article' 
RETURN a, b, count(p) as c, i''' % institution
                    
        relations = graph.run(query_relations).data()
        links = list()
        if len(relations) < 10:
            raise Exception("Few nodes")
        for r in relations:
            links.append({"source": r['a']["name"], 
                          "target": r['b']["name"], 
                          "size": 6,
                          "rel_count": r['c'],
                          "institution": Publication.colorcode(r['i']['name']) if r['i'] is not None else 'yellow'
                        })
        print("Modelo criado com %i arestas" % len(links))    
        return dict(children=links)
        
    def relationAuthorPublication(self):
        query_relations = "MATCH (a:Author)<-[r:AUTHORING]->(p:Publication) WHERE p.type='article' RETURN a,p"
        relations = graph.run(query_relations)
            
        links = list()
        if relations.__len__() < 10:
            raise Exception("Few nodes")
        for r in relations:
            links.append({"source": r[0]["name"],
                          "target": r[1]["key"],
                          "size": 6
                          })
            
        return dict(children=links)


class Institution(object):
    def __init__(self):
        pass

    @staticmethod
    def getInstitutionsName():
        return [inst['name'] for inst in graph.nodes.match("Institution")]

    @staticmethod
    def institutionInteraction():
        query = '''MATCH path=(i1:Institution)-[]-(a1:Author)-[]-(p:Publication)-[]-(a2:Author)-[]-(i2:Institution)
                WHERE id(i1) > id(i2)
                RETURN i1.name,i2.name, count(p)
                '''
        interaction = graph.run(query)
        interlist = list()
        for i in interaction:
            interlist.append({"source": i[0], "target": i[1], "rel_count": i[2]})
        return dict(result=interlist)


class GraphInfo(object):
    def __init__(self):
        if type(graph) is str:
            raise RuntimeError("Graph not connected")

    @staticmethod
    def node_count():
        return graph.run("MATCH (n) RETURN count(n) AS nodes").data()[0]['nodes']

    @staticmethod
    def rel_count():
        return graph.run("MATCH ()-[r]-() RETURN count(r) AS rels").data()[0]['rels']
        
    def avg_degree(self):
        num_nodes = GraphInfo.node_count()
        num_rels = GraphInfo.rel_count()
        return num_rels / num_nodes
        
    def betweenness(self):
        pass
        
    def closeness(self):
        pass
        
    def diameter(self):
        pass
        
    @lru_cache(maxsize=1024)    
    def distance(self, x, y):
        pass
