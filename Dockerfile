FROM python:3.9

WORKDIR /pipeline/

COPY requirements.txt /pipeline/requirements.txt
RUN pip install --no-cache-dir -r /pipeline/requirements.txt

ADD ekspiper ./pipeline/ekspiper
COPY server_container.py ./pipeline/

CMD ["python", "server_container.py", "--host", "0.0.0.0", "--port", "80"]
