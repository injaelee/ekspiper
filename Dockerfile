FROM python:3.9

ARG NETWORK
ARG STATE_PATH

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ekspiper ./ekspiper
COPY server_container.py .
RUN echo "network: $NETWORK" > /app/config.yml
RUN echo "state_path: $STATE_PATH" >> /app/config.yml

ENTRYPOINT ["python", "server_container.py", "-c", "/app/config.yml"]

#ENTRYPOINT python server_container.py -ft $NETWORK

