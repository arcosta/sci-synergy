"""Script to import data from dblp xml to neo4j graph database"""
from xml.sax import make_parser
import gzip
import time
import datetime
import json
import uuid
from multiprocessing import Process, Queue
import sys
import shutil
import os
import logging
from logging.handlers import RotatingFileHandler
from dblpcontent import DBLPContentHandler
from functools import lru_cache
# nltk está gerando um erro pois não está encontrando os drives D e E
from nltk import distance
from py2neo import Graph, Node, Relationship

if sys.version_info.major < 3:
    print("Please, use Python 3")
    sys.exit(-1)
CONFIG = ''

with open("configloader.json") as configFile:
    CONFIG = json.load(configFile)

FORMAT = '%(asctime)-15s %(threadName)s:  %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
logHandler = RotatingFileHandler("DBLPImport.log", 'a', maxBytes=5000000, backupCount=10)
logger.addHandler(logHandler)

URL = CONFIG['dblp.filename']
graph = Graph(CONFIG['neo4j.url'],
              username=CONFIG['neo4j.username'],
              password=CONFIG['neo4j.password'],
              bolt=True
             )

rootRepo = CONFIG["repo.root"]

# Create repository of cypher files
if not os.path.exists(rootRepo):
    logger.info("Creating repo dir " + rootRepo)
    os.mkdir(rootRepo)
else:
    if os.listdir(rootRepo) is not None:
        logger.info("Removing old files")
        shutil.rmtree(rootRepo)
        logger.info("Recreating repo dir: " + rootRepo)
        os.mkdir(rootRepo)


#================================================================
def loadAuthor():
    """Insert an author into graph"""
    seqAuthor = -1
    p = {
        'name':'Vanessa Tavares Nunes',
        'lattesurl':'http://lattes.cnpq.br/2043415661294559'
        }

    lastAuthorid = graph.run('''MATCH (a:Author)
    WHERE a.authorid is not null 
    RETURN a.authorid as authorid 
    ORDER BY authorid DESC limit 1'''
                            )

    if lastAuthorid:
        seqAuthor = lastAuthorid[0][0] + 1

    author = Node("Author",
                  name=p['name'],
                  lattesurl=p['lattesurl']
                 )
    author['authorid'] = seqAuthor

    graph.create(author)
    return [author]

#================================================================
def loadAuthorFilter():
    """
    @return A list of author names
    """
    profList = list()
    seqAuthor = 1

    filterFiles = ['docentes-unb.json',
                   'docentes-ufmg.json',
                   'docentes-ufrn.json',
                   'docentes-usp.json',
                   'docentes-ufam.json']

    lastAuthorid = graph.run('''MATCH (a:Author)
                             WHERE a.authorid is not null
                             RETURN a.authorid as authorid ORDER BY authorid DESC limit 1'''
                            )

    if lastAuthorid.current() is not None:
        seqAuthor = lastAuthorid.current() + 1

    for j in filterFiles:
        print("Loading filter %s" % j)
        instName = j.split('.')[0].split('-')[1]

        institution = graph.find_one("Institution", property_key='name',
                                     property_value=instName)
        if institution is None:
            institution = Node("Institution", name=instName)
            for p in json.load(open(j, 'r', encoding='latin-1')):
                if p is not None:
                    author = Node("Author", name=p['name'],
                                  lattesurl=p['lattesurl'])
                    author['authorid'] = seqAuthor

                    graph.create(author)
                    graph.create(Relationship(author, "ASSOCIATED TO", institution))
                    #del author
                    profList.append(author)
                    seqAuthor += 1
        else:
            print("\tFilter load SKIPPED")
            for rel in institution.match(rel_type='ASSOCIATED TO'):
                profList.append(rel.start_node())
        del institution
    
    return profList

def removeAccents(data):
    """Remove accents from input string"""
    translationTable = str.maketrans("çäáâãèéêíóôõöúñ", "caaaaeeeiooooun", ":'`{}[])(@?!_-/")
    return data.lower().translate(translationTable)

@lru_cache(maxsize=1024)
def compareNames(a, b):
    """Compare two names using a heuristic method"""
    dist_threshold = 11
    if a is None or b is None:
        return False
    if a == b:
        return True

    dist = distance.edit_distance(a, b)

    #if a.find('.') > 0 or b.find('.') > 0:
    if dist <= dist_threshold:
        a_list = a.split()
        b_list = b.split()
        if not a_list or not b_list:
            return False
        if a_list[0] == b_list[0] and a_list[-1] == b_list[-1]:
            return True
    else:
        return False

def createCypherFiles(queue):
    """"Creates cypher files to be inserted into graph"""
    logger = logging.getLogger('cypherWriter')

    while True:
        pubAttrs = queue.get()
        if pubAttrs == -1:
            break

        title = pubAttrs.get("title")
        pubKey = uuid.uuid4().__str__()
        logger.info("New publication title: %s" % title.encode('utf-8', errors='ignore'))
        query = ''

        for aName in pubAttrs["author"]:
            query += "MATCH (a:Author {name: '%s})' \n" % aName
            query += "MATCH (p:Publication {title: '%s'}) \n" % title
            query += "MERGE (a)-[r:AUTHORING]->(p)\n"
        with open(os.path.join(rootRepo, pubKey)+'.cypher', 'w', encoding='utf-8') as output:
            output.write(query)


def insertIntoGraph(queue):
    """Insert queue content into graph"""
    seqAuthor = 1
    
    #authorFilter = loadAuthor()
    #authorFilter = loadAuthorFilter()
    authorFilter = [node.name for node in graph.find("Author")]
    
    while True:
        pubAttrs = queue.get()
        if pubAttrs is None:
            break
        include = False
        if pubAttrs.get('author') is None:
            continue
        for author in pubAttrs.get('author'):
            author = author.strip()
            if [x for x in authorFilter if compareNames(removeAccents(x['name']), removeAccents(author))]:
                include = True
        
        if not include:
            continue
        newpub = graph.find_one("Publication", "title", pubAttrs.get("title"))
        if newpub is None:
            logging.info("Creating new publication" + pubAttrs.get("title", ""))
            newpub = Node()
            for att in pubAttrs.keys():
                newpub[att] = pubAttrs.get(att, -1)

            newpub.add_label('Publication')
            graph.create(newpub)
        else:
            continue

        for aName in list(pubAttrs['author']):
            author = None
            for authorNode in graph.find("Author"):
                if compareNames(removeAccents(authorNode['name']), removeAccents(aName)):
                    author = authorNode
                    break

            if author is None:
                author = Node("Author", name=aName)
                graph.create(author)
                logging.info("New author created: %s" % aName)
            relAuthoring = Relationship(author, "AUTHORING", newpub)
            logging.info("!!! Creating relationship: " + newpub.get('title'))
            graph.create(relAuthoring)
            
    print("All insertions done")


#================================================================
def main(source):
    """ main method"""
    print("Starting parse of file %s at %s" %(source, time.ctime()))
    loadAuthorFilter()

    start_time = time.time()
    queue = Queue()

    process_list = list()
    
    for _ in range(4):
        process_list.append(Process(target=insertIntoGraph, args=(queue,)))
        #process_list.append(Process(target=createCypherFiles, args=(queue,)))

    for process in process_list:
        process.start()

    source = gzip.open(source, mode='rt', encoding='latin-1')
    parser = make_parser()
    parser.setContentHandler(DBLPContentHandler(queue))
    parser.parse(source)

    queue.join_thread()

    #TODO: Make a test, with this instructions all processes never end.
    #for process in process_list:
    #    process.join()
    #    logging.info("Consumer terminated")

    elapsed_time = time.time() - start_time
    print("Execution time ", datetime.timedelta(seconds=elapsed_time))
    print("Finish")

if __name__ == "__main__":
    main(URL)
