FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.3

# install pip and postgresql header (libpq-dev) so pycog2 will install.
#
# python-rtree was NOT required building on Linux/GitLab CI. If it's missing
# during build on macOS/M1 the container won't run. Why? Probably due to
# arm64 emulation thins for the container?
#
# postgresql-client: Installs pg_dump/pg_restore used for dumping/importing database backups
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-rtree \
    libpq-dev \
    rsync \
    wget \
    postgresql-client \
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
