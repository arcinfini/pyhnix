FROM python:3.8-slim as base

WORKDIR /bot

ENV DISCORD_VENV=".venv"
RUN python -m venv $DISCORD_VENV
ENV PATH="$DISCORD_VENV/bin:$PATH"

FROM base as install

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

FROM install

COPY . .
CMD python3 main.py
