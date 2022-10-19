FROM python:3.8-slim

WORKDIR /bot

RUN apt-get -y update
RUN apt-get -y install git

ENV DISCORD_VENV=".venv"
RUN python -m venv $DISCORD_VENV
ENV PATH="$DISCORD_VENV/bin:$PATH"

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python3", "main.py"]

# according to this page, this syntax for starting a command allows it to be
# pid 1 which then means it receives the sigterm signal
