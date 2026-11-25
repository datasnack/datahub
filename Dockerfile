# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

# GDAL 3.13 has Ubuntu 26 with Python 3.14
FROM python:3.14-slim AS build
WORKDIR /src
COPY . .
RUN pip wheel --no-deps -w /wheels .

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.13.3

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-venv \
    python3-dev \
    rsync \
    wget \
    nginx \
    # postgresql-client has to match with the PostgreSQL server, in our case v18.
    # Ubuntu 26 installs v18 so we are good. It's used for dumping/importing the database
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# In accordance with PEP668 we create a venv for our dependencies, which is also the
# the default for Ubuntu 24.x that is used in gdal image since 3.9.x
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --upgrade pip

# Install Data Hub dependencies
COPY requirements.txt /opt/datahub/constraints.txt
RUN /opt/venv/bin/pip install --no-cache-dir --require-hashes -r /opt/datahub/constraints.txt
# Install Data Hub wheel
COPY --from=build /wheels /wheels
RUN /opt/venv/bin/pip install --no-cache-dir --no-index --no-deps /wheels/*.whl && rm -rf /wheels



COPY entrypoint.sh /opt/datahub/entrypoint.sh

# Prepare image for dependant project
RUN mkdir -p /app
WORKDIR /app

# put "/app/src" into to site-packages folder inside the .venv, so the packages below /src of the
# actual project, will be discovered.
RUN echo /app/src > "$(/opt/venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')/app-src.pth"


COPY ./nginx.conf /etc/nginx/sites-enabled/default

EXPOSE 8000

# Activate the venv globally before we start our app in the entrypoint.sh
ENV PATH=/opt/venv/bin:$PATH
CMD ["/opt/datahub/entrypoint.sh"]
