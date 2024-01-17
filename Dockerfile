FROM python:3.11-slim-bullseye

EXPOSE 8080

RUN python -m venv /opt/venv

COPY App/ /App/
COPY requirements.txt .

RUN /opt/venv/bin/pip install -r requirements.txt

WORKDIR /App/

RUN /opt/venv/bin/python3 run.py --setup

CMD [ "/opt/venv/bin/python3", "run.py",  "--run" ]
