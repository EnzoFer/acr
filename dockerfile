FROM python:3.10-slim-bullseye
ENV FLASK_DEBUG=1
ENV PROD_DATABASE_URI=""
ENV PYTHONUNBUFFERED=1
ENV PATH=$PATH:/home/flaskapp/.local/bin

RUN useradd --create-home --home-dir /home/flaskapp flaskapp

WORKDIR /home/flaskapp
USER flaskapp
RUN mkdir app


COPY ./app.py .

ADD requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

#puerto por el que escucha la imagen
EXPOSE 5000
CMD [ "python", "./app.py" ]%