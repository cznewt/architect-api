FROM python:3

RUN apt-get update

WORKDIR /code/

# copy and install
COPY . .

WORKDIR /code/
RUN pip install -r requirements/base.txt

# run worker
CMD celery -A architect worker -l info
