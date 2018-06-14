FROM ubuntu:16.04

MAINTAINER Aurelio Costa "arcosta@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

# We copy just the requirements.txt first to leverage Docker cache

COPY ./code/web/requirements.txt ./app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./code/web /app

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]
