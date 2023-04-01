FROM python:3.9

WORKDIR /bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]

# https://www.ctl.io/developers/blog/post/gracefully-stopping-docker-containers/
# according to this page, this syntax for starting a command allows it to be
# pid 1 which then means it receives the sigterm signal
