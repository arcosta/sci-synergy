from openpyxl import load_workbook
from py2neo import Graph, Node, Relationship
from nltk import distance, stem, tokenize
SOURCEXLS = "20160613-JCR.xlsx"

class Entity(object):
    def __init__(self, title='', cites='', jcr=''):
        self.title = title
        self.cites = cites
        self.jcr = jcr
    def __str__(self):
        return "%s %s  %s" %(self.title, self.cites, self.jcr)
        

class JCRTable(object):
    def __init__(self):
        self.entities = list()
        self.loaded = False
        
    def loadTable(self):
        wb = load_workbook(SOURCEXLS)
        sheet_ranges = wb['DJR_9157']
        rowid = 4
        
        while True:        
            title = sheet_ranges['B'+str(rowid)].value
            if title is None:
                break
            cites = sheet_ranges['C'+str(rowid)].value
            jcr = sheet_ranges['E'+str(rowid)].value
            self.entities.append(Entity(title, cites, jcr))
            rowid += 1
        self.loaded = True
        
    def find(self, title):
        for entity in self.entities:
            if entity.title.lower().find(title.lower()) >=0:
                yield entity
        return None
def normalize(s):
    stemmer = stem.PorterStemmer()
    words = tokenize.wordpunct_tokenize(s.lower().strip())
    return ' '.join([stemmer.stem(w) for w in words])
 
def fuzzy_match(s1, s2, max_dist=3):
    '''
    from: https://streamhacker.com/2011/10/31/fuzzy-string-matching-python/
    '''
    return distance.edit_distance(normalize(s1), normalize(s2)) <= max_dist
    
def assignJCR(table):
    #TODO: Usar a heuristica apenas se o titulo tiver '.'
    if not table.loaded:
        print('Table not loaded')
        return
    g = Graph(username='scisynergy', password='scisynergy')
    for publication in g.find('Publication', 'type', 'article'):
        if not publication['journal']:
            continue
        distances = list()
        for jcrpub in table.entities:
            if publication['journal'].find('.') > 0 or jcrpub.title.find('.') > 0:
                if fuzzy_match(publication['journal'], jcrpub.title, 6):
                    print("Match: " + publication['journal'] + ' AND ' + jcrpub.title)
                    insertJCR(g, publication, jcrpub)
            else:
                if publication['journal'] == jcrpub.title:
                    print("Match: " + publication['journal'] + ' AND ' + jcrpub.title)
                    insertJCR(g, publication, jcrpub)

def insertJCR(graph, publication, jcrpub):
    #publication['jcr'] = jcrpub.jcr
    #graph.push(publication)
    
    journal = graph.find_one('Journal', 'title', jcrpub.title)
    if not journal:
        journal = Node('Journal', title = jcrpub.title, jcr = jcrpub.jcr, cites = jcrpub.cites)
        graph.create(journal)
    
    rel = Relationship(publication,'PUBLISHED', journal, year=publication['year'])
    graph.create(rel)
if __name__ == "__main__":
    table = JCRTable()
    table.loadTable()
    print("JCR Table loaded")
    
    choice = ''
    #while True:
    #    choice = input('Busca>')
    #    if choice == 'exit':
    #        print("Quiting ...")
    #        break
    #    
    #    [print(x) for x in table.find(choice)]
    assignJCR(table)