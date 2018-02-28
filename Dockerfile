FROM python:3

WORKDIR /code/

# copy and install
COPY . .
RUN pip install -r requirements/base.txt

# run app
CMD ./entrypoint.sh
