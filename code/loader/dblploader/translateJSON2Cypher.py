import os
import sys
import json

cypher = "seeds.cql"

for file in os.listdir(os.getcwd()):
    if file.find("docentes-") >= 0:
        with open(cypher, "a", encoding="utf-8") as fout:
            institution = file.split("-")[1].split(".")[0]
            fout.write("CREATE(n:Institution {name: '%s'});\n" % institution)
            with open(file, "r") as fin:
                jsonData = json.load(fin)
                for entry in jsonData:
                    if entry is None:
                        continue
                    fout.write("CREATE(a:Author {")
                    firstKey = True
                    for key in entry.keys():
                        if firstKey is True:
                            fout.write("%s: '%s'" % (key, entry.get(key)))
                            firstKey = False
                        else:
                            fout.write(", %s: '%s'" % (key, entry.get(key)))
                    fout.write("});\n")
                    fout.write("MATCH(i:Institution {name: '%s'}),(a:Author {name: '%s'}) MERGE (a)-[r:`ASSOCIATED TO`]->(i);\n" %(institution, entry.get('name')))
            
        