FROM python:3

WORKDIR /code/

# copy and install
COPY . .

WORKDIR /code/
RUN pip install -r requirements/base.txt

# run api
CMD ./api.entrypoint.sh
