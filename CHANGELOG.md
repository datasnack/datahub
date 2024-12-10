# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.2](https://github.com/datasnack/datahub/compare/v0.5.1..v0.5.2) - 2024-12-10

### Fixed

- Allow graceful default for get_property ([4d352a9](https://github.com/datasnack/datahub/commit/4d352a93df5bcbcdd8a324ab7c0b01ceaf57ff40))
- dl_init command handles case if data is already present in DB ([020a576](https://github.com/datasnack/datahub/commit/020a57674917c18da3175d16305b0e30626fee1c))
- Make sure leaflet popup is not larger than map area ([08bb6b5](https://github.com/datasnack/datahub/commit/08bb6b53f90c917b906ff2e6b5d5ab586024c524))

## [0.5.1](https://github.com/datasnack/datahub/compare/v0.4.2..v0.5.1) - 2024-12-10

This release brings a date picker on top of the Data Layer value list. Additionally, a simple import/export system for Data Layer specifications in the backend is provided.

Release v0.5.0 had missing dependencies in the release.

### Changed

- Markdown parsing for descriptions ([861cf73](https://github.com/datasnack/datahub/commit/861cf737c788e785fb45f8e4a0fbc3b895107cda))
- Value table allows temporal selection ([d6ae0f2](https://github.com/datasnack/datahub/commit/d6ae0f2c710ffabda22f974f397272ef759fa2ad))
- Allow import/export based on django serialization ([d8b748b](https://github.com/datasnack/datahub/commit/d8b748b75a15201bcea1330d83217a1ce8875266))

### Fixed

- If no data directory is present, the creation of the log dir would raise an exception. Make sure intermediate folders are created ([d8868f2](https://github.com/datasnack/datahub/commit/d8868f268ea65b2dec26b3bdd89fe3a60ff71618))

## [0.4.2](https://github.com/datasnack/datahub/compare/v0.4.1..v0.4.2) - 2024-11-25

### Fixed

- Regression, add dl key to allow searching for it in tables ([1949688](https://github.com/datasnack/datahub/commit/1949688b7e5cf7fa7501bfbfe425a7e47ff92d83))
- Cascade datalayer delete to log table, don't prevent ([6d048ac](https://github.com/datasnack/datahub/commit/6d048ac5c321b2d1232fdd33a0d9eb80f5ccf1b8))

## [0.4.1](https://github.com/datasnack/datahub/compare/v0.4.0..v0.4.1) - 2024-11-25

### Fixed

- Visually show derived/matching value in DL table ([1c0a79a](https://github.com/datasnack/datahub/commit/1c0a79a2dc78066b454fb65fc9b2911f70e8af3c))

## [0.4.0](https://github.com/datasnack/datahub/compare/v0.3.3..v0.4.0) - 2024-11-22

This release brings derived values to the Data Layer table views. If a value is not present for a given timestamp + shape, a parent shape and/or older value is derived.

### Changed

- Mgmt command to create data layer table indices ([41e1338](https://github.com/datasnack/datahub/commit/41e13383f9c120ff4f808cf2289e527e6014760e))
- Allow apps to append own items to navigation ([b477e06](https://github.com/datasnack/datahub/commit/b477e0626e1a591952cd815bd8fbe3a4443db7eb))
- Properties and shape geometries getter in Shape model ([09da45b](https://github.com/datasnack/datahub/commit/09da45bad9deaa4febd886620baf71f6c976bd5a))
- Rework picker layout and allow timestamp selection ([49156b8](https://github.com/datasnack/datahub/commit/49156b8ff57c9096a4a7da69add24efa33636cf2))
- Show spatial and temporal derived values ([72832d9](https://github.com/datasnack/datahub/commit/72832d9e080b227f8661c59a9d5716162a795dcd))

### Fixed

- Don't save pandas index to Data Layer table ([c1d2750](https://github.com/datasnack/datahub/commit/c1d2750a9c12be19e90643aca76444471d62cd5d))
- Catch uncovered tiff + handle GeoTiff scale factor ([bfbc262](https://github.com/datasnack/datahub/commit/bfbc26298256ccea201aacbabf4a3816056a661b))
- Provide wrapper to dynamically load plotly from outside build process ([89cc1e4](https://github.com/datasnack/datahub/commit/89cc1e49a8ea8aa533ac81554c0e1df9bb94950f))

## [0.3.3](https://github.com/datasnack/datahub/compare/v0.3.2..v0.3.3) - 2024-11-19

### Added

- Add json format for datalayer api ([44791fb](https://github.com/datasnack/datahub/commit/44791fb6b26f4d1c20d4524a43b0e9968e08d816))


### Fixed

- `robots.txt` to hint crawlers ([df7a06c](https://github.com/datasnack/datahub/commit/df7a06c746c5662faaa41cbd6103c797274b4a1f))
- Sane date default formatting in ISO8601 for Django templates ([e69b364](https://github.com/datasnack/datahub/commit/e69b3642823149aedfab1102dc5ea5c00746168e))
- Prevent pandas warning by using SQLAlchemy instead of psycopg Django connection object ([126fb04](https://github.com/datasnack/datahub/commit/126fb0450f955c172486e6e48ea26e3202bd6219))

## [0.3.2](https://github.com/datasnack/datahub/compare/v0.3.1..v0.3.2) - 2024-11-05

### Changed

- Use Data Layer key in download links ([731fdf9](https://github.com/datasnack/datahub/commit/731fdf9aa61b5573dec445bbcea0d2b0621f2ab2))
- Scaffolding command to create a new app ([be9e0a3](https://github.com/datasnack/datahub/commit/be9e0a3f3a25f61b062b5e8970ca3931f5c2279d))

### Fixed

- Tell bots to not crawl `/api/` routes ([03d96ee](https://github.com/datasnack/datahub/commit/03d96ee98bc8019674fb8d32e6f8eb64e6f8edd5))

## [0.3.1](https://github.com/datasnack/datahub/compare/v0.3.0..v0.3.1) - 2024-10-29

### Fixed

- Regression not showing Data Layers on Shape detail if local data are not available ([65c9a7e](https://github.com/datasnack/datahub/commit/65c9a7e0767248f9664b3ade7ff5d00e14a6ebee))

## [0.3.0](https://github.com/datasnack/datahub/compare/v0.2.0..v0.3.0) - 2024-10-28


## [0.2.0](https://github.com/datasnack/datahub/compare/v0.1.0.dev1..v0.2.0) - 2024-05-23


<!-- generated by git-cliff -->
