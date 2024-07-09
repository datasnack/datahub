FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.1

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-venv \
    python3-dev \
    rsync \
    wget \
    nginx \
    # postgresql-client has to match with the PostgreSQL server, in our case v16.
    # Ubuntu 24 installs v16 so we are good. It's used for dumping/importing the database
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# In accordance with PEP668 we create a venv for our dependencies, which is also the
# the default for Ubuntu 24.x that is used in gdal image since 3.9.x
RUN python -m venv /opt/datahub/venv \
    && /opt/datahub/venv/bin/python -m pip install --upgrade pip

# To leverage Docker layer caching we copy the requirements.txt and install it and copy
# the rest of our files after, so during build the pip install is only executed when
# the requirements.txt changed
RUN mkdir -p /app
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN /opt/datahub/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . /app


COPY ./nginx.conf /etc/nginx/sites-enabled/default

EXPOSE 8000

# Activate the venv globally before we start our app in the entrypoint.sh
ENV PATH=/opt/datahub/venv/bin:$PATH
CMD ["./entrypoint.sh"]
