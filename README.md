# Data Hub

The Data Hub is a geographic information system (GIS) with a data fusion engine for harmonizing diverse data sources. Its focus is to harmonize diverse data on temporal and spatial axes, to allow the user to combine and analyze this information.

See [this repository](https://github.com/datasnack/dh-ghana) for an example of the Data Hub software with a focus data available in Ghana.


## Installation

The recommended way to use the Data Hub is via Docker and to reference the image built from this repository. See the [Ghana Data Hub](https://github.com/datasnack/dh-ghana) example for installation steps. By doing so it allows for updating the core system independent of you customizations.

To install the Data Hub from source, follow these steps:

- Install a PostGIS database (you can use the provided Docker image from the `docker-compose.yml`).
- Create a `.env` file based on the `.env.example` file.
- Create a Python virtual environment with `python -m venv .venv` and activate it with `./.venv/bin/activate`.
- Install Python dependencies via `pip install -r requirements.txt` (might be complicated due to GDAL/PROJ dependencies).
- Run database migrations with `python manage.py migrate`
- Run Django with `python manage.py runserver`
- Create a new superuser with `python manage.py createsuperuser`

The system is now running and usable at [http://localhost:8000/](http://localhost:8000/), to use it:

- Import your Shapes with `python manage.py loadshapes <file>`
- Place your Data Layer source files in `src/datalayers/`
- Downloaded data will be placed in `data/datalayers/`


## License

MIT
