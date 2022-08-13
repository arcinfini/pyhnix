FROM python:3.8-slim

WORKDIR /bot

RUN apt-get -y update
RUN apt-get -y install git

# ENV DISCORD_VENV=".venv"
# RUN python -m venv $DISCORD_VENV
# ENV PATH="$DISCORD_VENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip --version

COPY . .
CMD python main.py
