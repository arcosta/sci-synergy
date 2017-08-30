from xml.sax import ContentHandler
import logging

class DBLPContentHandler(ContentHandler):
    """Handle xml database content"""
    inPublication = True
    currentPubName = ''
    attrs = {}
    value = ''

    def __init__(self, queue=''):
        super()
        
        self.queue = queue
        self.pubtypes = ['article',
            'inproceedings',
            'proceedings',
            'book',
            'incollection',
            'phdthesis',
            'mastersthesis']


    def startElement(self, name, attrs):
        try:
            if self.pubtypes.index(name) >= 0:
                DBLPContentHandler.inPublication = True
                DBLPContentHandler.currentPubName = name
                DBLPContentHandler.attrs['key'] = attrs['key']
        except ValueError as error:
            logging.debug(error)

    def endElement(self, name):
        if DBLPContentHandler.inPublication is True:
            if DBLPContentHandler.currentPubName == name:
                DBLPContentHandler.attrs["type"] = name
                self.queue.put(DBLPContentHandler.attrs)
                # Flush object                
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
    def endDocument(self):
        self.queue.close()
    
