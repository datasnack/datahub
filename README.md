# Data Hub

The Data Hub is a geographic information system (GIS) featuring a data fusion engine designed for data harmonization, alongside an interactive dashboard for effective data exploration and collaboration. Its key objective is to merge data of multiple formats and sources across temporal and spatial axes, allowing users to combine, analyze, and interpret the data.

In [this repository](https://github.com/datasnack/dh-ghana) you can explore an example setup of the Data Hub software tailored to data concerning Ghana.


## Installation

The recommended way to use the Data Hub is via Docker and to reference the image built from this repository. See the [Ghana Data Hub](https://github.com/datasnack/dh-ghana) example for installation steps. By doing so it allows for updating the core system independent of you customizations.

To install the Data Hub from source, follow these steps:

- Use at least Python v3.12.x
- Install a PostGIS v16.x database (you can use the provided Docker image from the `docker-compose.yml`).
- Create a `.env` file based on the `.env.example` file.
- Create a Python virtual environment with `python -m venv .venv` and activate it with `source .venv/bin/activate`.
- Install Python dependencies via `pip install -r requirements.txt` (might be complicated due to GDAL/PROJ dependencies).
- Run database migrations with `python manage.py migrate`
- Run Django with `python manage.py runserver`
- Create a new superuser with `python manage.py createsuperuser`

The system is now running and usable at [http://localhost:8000/](http://localhost:8000/), to use it:

- Import your Shapes with `python manage.py loadshapes <file>`
- Place your Data Layer source files in `src/datalayers/`
- Downloaded data will be placed in `data/datalayers/`


## Attributions

The Data Hub is an open-source software (OSS) developed through the [DiDEX](https://www.bnitm.de/forschung/forschungsgruppen/population/abt-infektionsepidemiologie/research-topics/surveillance-and-digital-epidemiology/didex) project (Digital Data and Exploratory Spaces for Strengthening Infectious Disease Research within the One Health nexus) at the Bernhard Nocht Institute for Tropical Medicine. The project is supported and funded by the Joachim Herz Foundation ("[Innovate! Academy](https://www.joachim-herz-stiftung.de/en/research/research-and-application/innovation-academy)" program).

The source code of the Data Hub is informed by the [results](https://github.com/MARS-Group-HAW/esida-db) of the ESIDA project.


## License

MIT
