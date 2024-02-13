FROM python:3.11-alpine as python-base

# Install gcc and other build dependencies.
# https://wiki.alpinelinux.org/wiki/GCC
# https://stackoverflow.com/questions/58393840/fatal-error-ffi-h-no-such-file-or-directory-on-pip2-install-pyopenssl
RUN apk add build-base libffi-dev

# https://gist.github.com/soof-golan/6ebb97a792ccd87816c0bda1e6e8b8c2
# Configure Poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

FROM python-base as poetry-base

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

FROM python-base as bot

# Copy poetry over and add to path
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-interaction --no-cache --without dev

COPY bot /app/bot
CMD ["poetry", "run", "python", "-m", "bot"]