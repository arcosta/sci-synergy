"""Script to import data from dblp xml to neo4j graph database"""
from xml.sax import make_parser, ContentHandler
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
# nltk está gerando um erro pois não está encontrando os drives D e E
from nltk.distance import edit_distance
from py2neo import Graph, Node, Relationship

if sys.version_info.major < 3:
    print("Please, use Python 3")
    sys.exit(-1)
CONFIG = ''

with open("configloader.json") as configFile:
    CONFIG = json.load(configFile)

FORMAT = '%(asctime)-15s %(process)d:  %(message)s'
logging.basicConfig(format=FORMAT, filename="DBLPImport.log", level='INFO')
logger = logging.getLogger('ROOT')

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


pubtypes = ['article',
            'inproceedings',
            'proceedings',
            'book',
            'incollection',
            'phdthesis',
            'mastersthesis']

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
                   'docentes-usp.json']

    lastAuthorid = graph.run('''MATCH (a:Author)
                             WHERE a.authorid is not null
                             RETURN a.authorid as authorid ORDER BY authorid DESC limit 1'''
                            )

    if lastAuthorid.current() is not None:
        seqAuthor = lastAuthorid.current() + 1

    for j in filterFiles:
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
        del institution
    print("Filters loaded")
    return profList

def removeAccents(data):
    """Remove accents from input string"""
    translationTable = str.maketrans("çäáâãèéêíóôõöúñ", "caaaaeeeiooooun", ": '`{}[])(@?!_-/")
    return data.lower().translate(translationTable)

def compareNames(a, b):
    """Compare two names using a heuristic method"""
    if a is None or b is None:
        return False
    if a == b:
        return True

    distance = edit_distance(a, b)

    #if a.find('.') > 0 or b.find('.') > 0:
    if distance <= 11:
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
    while True:
        pubAttrs = queue.get()
        if pubAttrs == -1:
            break
        newpub = graph.find_one("Publication", "title", pubAttrs.get("title"))
        if newpub is None:
            print("Creating new publication")
            for att in pubAttrs.keys():
                newpub[att] = pubAttrs.get(att, -1)

            newpub.labels.add('Publication')
            graph.create(newpub)
        else:
            continue

        # Look for the authors of the publication and if not found create the new nodes
        lastAuthorid = graph.run('''MATCH (a:Author)
                                 WHERE a.authorid is not null 
                                 RETURN a.authorid as authorid ORDER BY authorid DESC limit 1'''
                                )
        if lastAuthorid:
            seqAuthor = lastAuthorid[0][0] + 1

        for aName in list(pubAttrs['author']):
            author = None
            for authorNode in graph.find("Author"):
                if compareNames(removeAccents(authorNode['name']), removeAccents(aName)):
                    author = authorNode
                    break

            if not author:
                author = Node("Author", name=aName, authorid=seqAuthor)
                graph.create(author)
                print("New author created: %s" % aName)
                seqAuthor += 1
            relAuthoring = Relationship(author, "AUTHORING", newpub)
            graph.create(relAuthoring)
            print("Publication created: %s" % newpub['title'])
        time.sleep(2)
    print("All insertions done")

#================================================================
class DBLPContentHandler(ContentHandler):
    """Handle xml database content"""
    inPublication = True
    currentPubName = ''
    attrs = {}
    value = ''

    def __init__(self, queue=''):
        super()
        self.authorFilter = loadAuthorFilter()
        #self.authorFilter = loadAuthor()
        self.queue = queue

    def startElement(self, name, attrs):
        try:
            if pubtypes.index(name) >= 0:
                DBLPContentHandler.inPublication = True
                DBLPContentHandler.currentPubName = name
                DBLPContentHandler.attrs['key'] = attrs['key']
        except ValueError as error:
            error = ''

    def endElement(self, name):
        if DBLPContentHandler.inPublication is True:
            if DBLPContentHandler.currentPubName == name:
                DBLPContentHandler.attrs["type"] = name
                #filtering publications by author
                try:
                    for author in DBLPContentHandler.attrs['author']:
                        author = author.strip()
                        if [x for x in self.authorFilter if compareNames(removeAccents(x['name']),
                                                                         removeAccents(author))]:
                            self.queue.put(DBLPContentHandler.attrs)
                    # Flush object
                except KeyError as error:
                    error = ''

                DBLPContentHandler.inPublication = False
                DBLPContentHandler.attrs = {}
            else:
                if name == "author":
                    if DBLPContentHandler.attrs.get(name) is not None:
                        DBLPContentHandler.attrs[name].append(DBLPContentHandler.value.strip())
                    else:
                        DBLPContentHandler.attrs[name] = [DBLPContentHandler.value]
                else:
                    DBLPContentHandler.attrs[name] = DBLPContentHandler.value
        DBLPContentHandler.value = ''

    def characters(self, content):
        if content != '':
            DBLPContentHandler.value += content.replace('\n', '')

#================================================================
def main(source):
    """ main method"""
    print("Inicializando parse do arquivo %s em %s" %(source, time.ctime()))

    start_time = time.time()
    queue = Queue()

    process_list = list()
    for _ in range(4):
        #process_list.append(Process(target=insertIntoGraph, args=(q,)))
        process_list.append(Process(target=createCypherFiles, args=(queue,)))

    for process in process_list:
        process.start()

    source = gzip.open(source, mode='rt', encoding='latin-1')
    parser = make_parser()
    #parser.setFeature(handler.feature_external_ges, False);
    #parser.setFeature(handler.feature_validation, False)
    parser.setContentHandler(DBLPContentHandler(queue))
    parser.parse(source)
    # Flag for last element of queue, one for each queue consumer
    queue.put(-1)
    queue.put(-1)
    queue.put(-1)
    queue.put(-1)

    for process in process_list:
        process.join()

    elapsed_time = time.time() - start_time
    print("Tempo de execução ", datetime.timedelta(seconds=elapsed_time))
    print("Finish")

if __name__ == "__main__":
    main(URL)
