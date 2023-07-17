FROM python:3.9

ARG CASPIAN_BRONZE_KEY
ENV caspian_bronze_key=$CASPIAN_BRONZE_KEY

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ekspiper ./ekspiper
COPY server_container.py .
COPY config.yml .

RUN echo "Printing caspian bronze key"
RUN echo $caspian_bronze_key

ENTRYPOINT ["python", "server_container.py"]
CMD ["-c", "/app/config.yml"]
