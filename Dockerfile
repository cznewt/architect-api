FROM python:3

RUN apt-get update && \
apt-get install -y npm rubygems ruby-dev

RUN gem install sass --no-user-install

WORKDIR /code/

# copy and install
COPY . .

WORKDIR /code/architect-api/
RUN npm install || true

WORKDIR /code/
RUN pip install -r requirements/base.txt && pip install psycopg2-binary

RUN python manage.py collectstatic --noinput && \
python manage.py compress

# run app
CMD ./entrypoint.sh
