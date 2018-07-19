FROM python:3

MAINTAINER Aurelio Costa "arcosta@gmail.com"

# We copy just the requirements.txt first to leverage Docker cache

COPY ./requirements.txt ./app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENTRYPOINT [ "python" ]

CMD [ "main.py" ]
