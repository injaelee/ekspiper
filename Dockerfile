FROM python:3.9

ARG NETWORK

WORKDIR /pipeline/

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

ADD ekspiper ./ekspiper
COPY server_container.py ./

CMD python server_container.py -ft $NETWORK
