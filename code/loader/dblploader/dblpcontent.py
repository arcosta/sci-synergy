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
            logging.debug(error)

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
                    logging.debug(error)

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
