FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.4


# Ubuntu installs postgresql-client v14, but out server is already v16.
# So pg_dump/restore works the versions should match. So we install v16 of the
# client tools manually. For this we need to add the Postgresql repo/key first.
RUN apt-get update && apt-get install -y lsb-release gpg && apt-get clean all
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg

# install pip and postgresql header (libpq-dev) so pycog2 will install.
#
# python-rtree was NOT required building on Linux/GitLab CI. If it's missing
# during build on macOS/M1 the container won't run. Why? Probably due to
# arm64 emulation things for the container?
#
# postgresql-client: Installs pg_dump/pg_restore used for dumping/importing database backups
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-rtree \
    libpq-dev \
    rsync \
    wget \
    postgresql-client-16 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

RUN mkdir -p /app

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

EXPOSE 80

# parameter for ENTRYPOINT (i.e. docker run <image> <cmd> can be used to overwrite this)
#CMD ["gunicorn", "--bind", "0.0.0.0:80", "esida:app"]
CMD ["./entrypoint.sh"]



