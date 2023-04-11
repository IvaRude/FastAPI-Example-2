FROM snakepacker/python:3.11

WORKDIR /backend

# install system dependencies
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip
RUN pip install --upgrade pip


COPY ./requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY . ./backend

