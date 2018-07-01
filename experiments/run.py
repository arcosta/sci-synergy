import os
from subprocess import Popen, PIPE

neo4jpath = 'C:/devel/datagraph/neo4j-community-3.3.4/bin/'
neo4jcmd = 'neo4j.bat'
neo4jargs = ' console'

#Start Database
dbp = Popen(neo4jpath + neo4jcmd + neo4jargs, stdin=PIPE)
sts = os.waitpid(dbp.pid, 0)[1]

time.sleep(30)

print("OK")



