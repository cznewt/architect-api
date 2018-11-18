FROM python:3-slim

RUN pip install xonsh && \
    pip install pyyaml && \
    pip install fn.py && \
    pip install click && \
    pip install mypy-lang

RUN mkdir -p /root/.config/xonsh/  && \
    echo "{}" > /root/.config/xonsh/config.json

CMD xonsh
