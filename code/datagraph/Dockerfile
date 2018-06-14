FROM neo4j:3.3.2

LABEL version="1.0"

RUN chgrp -R 0 /var/lib/neo4j \
  && chmod -R g+rwX /var/lib/neo4j

RUN neo4j-admin set-initial-password scisynergy