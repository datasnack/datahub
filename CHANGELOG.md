<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.4](https://github.com/datasnack/datahub/compare/v0.11.3..v0.11.4) - 2026-01-12

### Changed

- Update api names ([a7386e3](https://github.com/datasnack/datahub/commit/a7386e30d60820e39e1fdb4b2fe9e4a247333cf8))
- Include shape details in data download + prefix dh specifc shape ID ([c3b81cc](https://github.com/datasnack/datahub/commit/c3b81cc4bdad044c988a6ecf8bb4c94da3cbe3c0))
- Switch from Leaflet to Maplibre ([e8e5d3d](https://github.com/datasnack/datahub/commit/e8e5d3dc22f581112d772bff08a71af9ce4236f4))

### Fixed

- Only show admin link if user has permission ([67618cf](https://github.com/datasnack/datahub/commit/67618cff9b34246ade4e162d9a60c31563926796))
- Front permission key in template ([d51c62b](https://github.com/datasnack/datahub/commit/d51c62be2b926361a274510845159ba44f4ec551))
- Area is not a NONULL value, if it's not available return None ([3c744bf](https://github.com/datasnack/datahub/commit/3c744bfd5dabc90af1d2ed84ba6d735a0aab2782))
- Plotly aggregation not possible for binary type ([2908dbc](https://github.com/datasnack/datahub/commit/2908dbc68ef91a870663a7a1e5bbe63ea1a6ef08))

## [0.11.3](https://github.com/datasnack/datahub/compare/v0.11.2..v0.11.3) - 2025-11-20

### Fixed

- Show database unit in overview tables ([fb7286d](https://github.com/datasnack/datahub/commit/fb7286ded136d40395f8d6c06944a361e01fdf5b))
- Fallback for unavailable shape data ([5137f21](https://github.com/datasnack/datahub/commit/5137f21fdfb67b5d8c7ce38440b6c601002b998d))

## [0.11.2](https://github.com/datasnack/datahub/compare/v0.11.1..v0.11.2) - 2025-11-20

### Fixed

- Use correct "middle dot" unicode character ([8385f4b](https://github.com/datasnack/datahub/commit/8385f4b4eea28e080eb57492fc9c6ac70628f6bf))
- Show actual url loading error for apps ([fae3ebd](https://github.com/datasnack/datahub/commit/fae3ebde3770d500d3e9875e296ced1faef0f74a))
- Counter strange django-ninja url error ([4407b67](https://github.com/datasnack/datahub/commit/4407b67b221af00541e1f40d39f599a0ac701895))
- Value rounding for FLOAT type datalayers in frontend ([7202f86](https://github.com/datasnack/datahub/commit/7202f863acbb149709106675c53d1e3d9b67e613))

## [0.11.1](https://github.com/datasnack/datahub/compare/v0.11.0..v0.11.1) - 2025-11-13

### Changed

- MapLibre based map chart component ([ab126d7](https://github.com/datasnack/datahub/commit/ab126d77fdcbce204db67f051a7ebee6c3ec457f))
- Rework plotly chart component ([c98eaa7](https://github.com/datasnack/datahub/commit/c98eaa7812ee883a55285a091ca1a42269e41aa1))
- Configurable chart type (line/bar) ([e2972ef](https://github.com/datasnack/datahub/commit/e2972efa2de2ce346d5598439c5af8b1ead5c6d8))

### Fixed

- Cast year for end_date in data() ([e6f9000](https://github.com/datasnack/datahub/commit/e6f9000cea9862214b091fa2d0ec86ae5887e07f))
- Return parent id in shapes api, to allow aggregation on client ([772afd8](https://github.com/datasnack/datahub/commit/772afd86b70cbe2d582c57418725ffc0f22e6d3e))
- Use Data Snack logo as favicon ([49dbb69](https://github.com/datasnack/datahub/commit/49dbb69d97a3d85599c1a164d0477a2864977ff7))
- Use plotly error_y insteaf of sparate min/max lines ([372b988](https://github.com/datasnack/datahub/commit/372b988c082ca3208b7f940ff7543961e6110373))

### Removed

- Remove static file dir of md images, are downloaded directly view custom view ([763ea0c](https://github.com/datasnack/datahub/commit/763ea0c09efdbbfa88a6c6e56fa97ddef288c807))

## [0.11.0](https://github.com/datasnack/datahub/compare/v0.10.4..v0.11.0) - 2025-10-20

### Changed

- Switch license to AGPLv3 and clarify contributing
- Implement [REUSE](https://reuse.software/) guidelines

## [0.10.4](https://github.com/datasnack/datahub/compare/v0.10.3..v0.10.4) - 2025-10-13

- Update npm deps

## [0.10.3](https://github.com/datasnack/datahub/compare/v0.10.2..v0.10.3) - 2025-10-13

### Changed

- Load md images directly, not via static files ([6510354](https://github.com/datasnack/datahub/commit/6510354bfed491d65adbf872e2a5cd70e4c920f9))
- Streamline Data Layer management commands ([59d5b3f](https://github.com/datasnack/datahub/commit/59d5b3fe4686d7b489f49101855b0dd6e946b250))
- Build JavaScript/CSS assets in CI

### Fixed

- Autoselect first autocomplete item ([bad08b3](https://github.com/datasnack/datahub/commit/bad08b368649a51a1f64e30b142bbcd539df4c8f))
- Format shapes/Datalayers in autocomplete ([a677455](https://github.com/datasnack/datahub/commit/a677455473915702e568610d8537f1a793120e05))

## [0.10.2](https://github.com/datasnack/datahub/compare/v0.10.1..v0.10.2) - 2025-09-16

### Changed

- Use shape key as slug for urls instead of id ([bacbe7c](https://github.com/datasnack/datahub/commit/bacbe7cc623886f92a50113ca614b4d6f29a449f))

### Fixed

- Visual fixes, show username in user dropdown ([b004191](https://github.com/datasnack/datahub/commit/b004191328c67081d570972a35b68073cc055d14))
- Redirect for already authenticated users if they open the login page ([c5573ae](https://github.com/datasnack/datahub/commit/c5573ae059291a1a7eb75f3fc686f5c2abe32e8d))

## [0.10.1](https://github.com/datasnack/datahub/compare/v0.10.0..v0.10.1) - 2025-08-26

### Changed

- Provide CLI commands for resetting processed data ([b4646be](https://github.com/datasnack/datahub/commit/b4646beca463bfd8a51e966ca163dfc71e88ffe3))
- Make swap command extendable with configs ([0963c56](https://github.com/datasnack/datahub/commit/0963c56ed0e62701fb1795204c9ab66f905828e4))

### Fixed

- Show percentage of all known shape types, not only from available ([4cf1b22](https://github.com/datasnack/datahub/commit/4cf1b222a330869a9b0bf2ca362022c2847ebef4))
- Cast admin column to int/null ([ab62171](https://github.com/datasnack/datahub/commit/ab621715d275439b8aa58fb26b16b70afd67966f))
- Sources were not copied ([c753910](https://github.com/datasnack/datahub/commit/c7539106d0940703083200d7d590d99e52441839))


## [0.10.0](https://github.com/datasnack/datahub/compare/v0.9.7..v0.10.0) - 2025-07-29

### Changed

- Update snippet of api suggestions ([5c67d7e](https://github.com/datasnack/datahub/commit/5c67d7e337b3f78391b3d5e003079d81e581b70f))
- Switch to django-ninja for API ([c92d873](https://github.com/datasnack/datahub/commit/c92d87363d7f93b4dc965f8094154f95fa9dfda2))

## [0.9.7](https://github.com/datasnack/datahub/compare/v0.9.6..v0.9.7) - 2025-07-23

### Added

- Add netcfd and rioxarray deps for nc file processing ([7134d3f](https://github.com/datasnack/datahub/commit/7134d3f6b95c874dcf93a4d812f444c585b86d1b))
- Add urn pid type ([151896b](https://github.com/datasnack/datahub/commit/151896b1eb606d2877fd0fd9213557a0a91bd40b))

## [0.9.6](https://github.com/datasnack/datahub/compare/v0.9.5..v0.9.6) - 2025-07-21

### Changed

- Allow data layer filter for temporal type  by [Y], etc ([c6bf249](https://github.com/datasnack/datahub/commit/c6bf249bd0643ff410f7fcf7eddf490ddc50e277))

### Fixed

- Image max width on docs pages ([9c2fbc4](https://github.com/datasnack/datahub/commit/9c2fbc424436cd1c5ebb0e8c5d92f7cf5efa4e4e))
- Check for tregex first in dl selection for dl_download/process ([808d5ec](https://github.com/datasnack/datahub/commit/808d5ec4ca50fff556c1d6c5f6ab591c2ba9cd78))
- Missing week in epxected value for week ([6f79054](https://github.com/datasnack/datahub/commit/6f79054f90512ae900daa2992d3891984945d1b6))
- Catch ctrl+c in swap command to prevent stacktrace on abort ([b131c5f](https://github.com/datasnack/datahub/commit/b131c5f78f9f371597704786960b7694a3c7bcb6))
- Fix typos ([9b393c8](https://github.com/datasnack/datahub/commit/9b393c8867568fcac495b985565fd12a3819db35))

## [0.9.5](https://github.com/datasnack/datahub/compare/v0.9.4..v0.9.5) - 2025-07-02

### Fixed

- Update year in citation ([c722121](https://github.com/datasnack/datahub/commit/c722121cc2f55e2a0ff6cae50a93752901d9ac22))


## [0.9.4](https://github.com/datasnack/datahub/compare/v0.9.3..v0.9.4) - 2025-06-26

### Changed

- Use dl key instead of id for loading vector data ([7d96316](https://github.com/datasnack/datahub/commit/7d96316550dcb54c7a1abbc1bf1aa2589abb004f))

### Fixed

- Capitalize language names in dropdown ([340fb5d](https://github.com/datasnack/datahub/commit/340fb5dfb03fd04972352a5030a14e1c0c0e3210))

## [0.9.3](https://github.com/datasnack/datahub/compare/v0.9.2..v0.9.3) - 2025-06-26

### Fixed

- Requirements.txt was not committed ([5f56172](https://github.com/datasnack/datahub/commit/5f5617239bfeaa94aa99d29709b38953d5c38930))

## [0.9.2](https://github.com/datasnack/datahub/compare/v0.9.1..v0.9.2) - 2025-06-26

### Added

- Localized docs pages, home page can be set with markdown ([98743c4](https://github.com/datasnack/datahub/commit/98743c4632a2c57376e4afc4f10d55759644120c))
- Add icon for week temporal resolution ([bd7ba5f](https://github.com/datasnack/datahub/commit/bd7ba5f672a1e26165e89f60a44208d2cea25d68))
- Has_value function ([f2512b5](https://github.com/datasnack/datahub/commit/f2512b5654c767e493d94cf9156c68ccc104a335))
- Copy to clipboard via request, used for GeoJSON/WKT geometries ([45c1457](https://github.com/datasnack/datahub/commit/45c1457cad02bcce0bb565f4c40020f8ed8dcabe))

### Changed

- Use biome js for linting/formatting JavsScript ([2cab131](https://github.com/datasnack/datahub/commit/2cab13101d4ec75264caf055274d085f0fbcab9c))
- Move svgs to resource folder, update octicons, split octicons from other icons ([bfa54b4](https://github.com/datasnack/datahub/commit/bfa54b48ef6a7165c2c86495d554f72fbace82b2))

### Fixed

- Api call for bbox ([2e93010](https://github.com/datasnack/datahub/commit/2e930108ddcad89a22afd19bf19973d6ce9e02ca))
- Prevent lefleat controls overlapping the Bootstrap dropdowns ([a3a6902](https://github.com/datasnack/datahub/commit/a3a69027901b630f8fc690f29d801a363a0008f5))

## [0.9.1](https://github.com/datasnack/datahub/compare/v0.9.0..v0.9.1) - 2025-06-14

### Fixed

- Regression values on heatmap not shown ([a3468c3](https://github.com/datasnack/datahub/commit/a3468c3b4679bd1146a4904e8d84b1f5fd4c7cc9))

## [0.9.0](https://github.com/datasnack/datahub/compare/v0.8.10..v0.9.0) - 2025-06-11

- Switch navigation from top to sidebar nav with offcanvas.
- Provide simple markdown file based documentation section

### Changed

- Simple markdown file based docs section ([ac087a0](https://github.com/datasnack/datahub/commit/ac087a004960287388206a947e53cb6d0d323a59))
- Show shape key in list/detail views ([b7b591a](https://github.com/datasnack/datahub/commit/b7b591a8f5ffe1c31bdce27661f25e5be1c97e41))
- Prefetch categories and tags ([c769ca2](https://github.com/datasnack/datahub/commit/c769ca26fac42de6e513162200dcae4b9264ad8e))
- Move navbar to sidebar nav + offcanvas ([de8e77e](https://github.com/datasnack/datahub/commit/de8e77eadc43d840a92e63bbbfe266b6f7997ca7))

### Fixed

- Search shapes also by key ([738d8ce](https://github.com/datasnack/datahub/commit/738d8ce956c3117a37ef3e57e0df77a4d76d54a1))
- Dynamic data layer list view title dependeing on filter ([7729ade](https://github.com/datasnack/datahub/commit/7729ade5eb0b221ea6821c8cd2e57b700140db78))
- Return all shapes for shape API if no filter is present ([877d599](https://github.com/datasnack/datahub/commit/877d599fa4025557c185bfeb178e0cb1da414b03))
- Provide shape key in download ([500b1c7](https://github.com/datasnack/datahub/commit/500b1c7bc698cb41efa3d87b62898d855927b690))

## [0.8.10](https://github.com/datasnack/datahub/compare/v0.8.9..v0.8.10) - 2025-05-23

### Fixed

- Check got geottiff extension *.geotiff ([37d6f04](https://github.com/datasnack/datahub/commit/37d6f04583cf2b02153612045c45ec523832ab0e))


## [0.8.9](https://github.com/datasnack/datahub/compare/v0.8.8..v0.8.9) - 2025-05-22

### Changed

- Week type ([3cdd286](https://github.com/datasnack/datahub/commit/3cdd286c259ef959cd7abc5035cbf058407dd883))
- Error log helper ([896157a](https://github.com/datasnack/datahub/commit/896157ac9601b510fb8af746264512209b4bf88f))

### Fixed

- Cast to list() to prevent dict.values() type ([fcd36d1](https://github.com/datasnack/datahub/commit/fcd36d19ffd66ae600c59bbeb10ec053df2ae6fa))

## [0.8.8](https://github.com/datasnack/datahub/compare/v0.8.7..v0.8.8) - 2025-05-20

### Fixed

- @deprected is python 3.13, container is still in 3.12… ([afd86a6](https://github.com/datasnack/datahub/commit/afd86a60b180657ff6af5780cbaf75fd87b81d00))

## [0.8.7](https://github.com/datasnack/datahub/compare/v0.8.6..v0.8.7) - 2025-05-20

Categorical Data Layer Types (NOMINAL, ORDINAL), `add_value()` function to simplify data layer processing.

### Added

- Add_value function with validation in baselayer ([1b00c3a](https://github.com/datasnack/datahub/commit/1b00c3a2849c24f62a4e5e45b2685b3dbda3e5c0))
- Add --dry-run option to processing ([7b190e6](https://github.com/datasnack/datahub/commit/7b190e654e479edaf6115892b1dd5cf6275f1ffc))

### Changed

- Show instance changelog ([e7e2313](https://github.com/datasnack/datahub/commit/e7e2313dbd40344731d5eeefa15914a33e13bbbb))

### Fixed

- Prep categorical values for map viz ([42ecbc4](https://github.com/datasnack/datahub/commit/42ecbc4e416279cc7fbaa366853c19dd0f9affb2))
- Datalayer model uses same instance of base layer class during life cycle ([e97a3e5](https://github.com/datasnack/datahub/commit/e97a3e5bae947cbda01bf16644e7ea02279f15f3))
- Update scaffolding data layer to latest spec ([94e89bd](https://github.com/datasnack/datahub/commit/94e89bd91147cbf55821169766eb1701eb763c74))
- Remove , introtduced due to list joining ([1c158a4](https://github.com/datasnack/datahub/commit/1c158a480f719580eab460526a030277a2e1b618))

## [0.8.6](https://github.com/datasnack/datahub/compare/v0.8.5..v0.8.6) - 2025-04-28

### Added

- Add gpxpy for gpx based data layers ([12950fd](https://github.com/datasnack/datahub/commit/12950fdf60543d8fc69e6d5b5c2e488bd28f75e7))

### Changed

- Inject all shapes as default into dl_process hook ([96e8ad3](https://github.com/datasnack/datahub/commit/96e8ad3ab58ab77c2616e70b9b6ea01b89542cb0))
- Month based data layers ([bdd41e7](https://github.com/datasnack/datahub/commit/bdd41e765156a8433e2a6445416ab0e838cdfd7a))
- Categorical value types (nominal, ordinal) ([c075275](https://github.com/datasnack/datahub/commit/c075275592819aa3d224821e88bf6dabe5e9187c))


## [0.8.5](https://github.com/datasnack/datahub/compare/v0.8.4..v0.8.5) - 2025-04-16

### Changed

- Allow loadshapes to truncate Shapes before import ([a4ba09f](https://github.com/datasnack/datahub/commit/a4ba09f4201380a48556ce9267033b0db0974c38))

### Fixed

- During loadshapes reuse ShapeType with same key ([57a5e28](https://github.com/datasnack/datahub/commit/57a5e28f0895df78261d800396e027104ea88bcb))

## [0.8.4](https://github.com/datasnack/datahub/compare/v0.8.3..v0.8.4) - 2025-03-19

### Added

- Add more information about API access, add token infos ([93e8f95](https://github.com/datasnack/datahub/commit/93e8f95befa2a582c76b463e8d1abb6d345c90b8))

### Fixed

- Cast simplify parameter in shapes API ([853d2aa](https://github.com/datasnack/datahub/commit/853d2aa63daf442e178105608da15e58af8c1002))

## [0.8.3](https://github.com/datasnack/datahub/compare/v0.8.2..v0.8.3) - 2025-03-18

### Fixed

- Don't write pandas index to database ([dd6dfa8](https://github.com/datasnack/datahub/commit/dd6dfa8601d5a65ac8ba473b6bfb9ca07eff4e53))
- Import further scale since Legend depends on them in some cases ([f718337](https://github.com/datasnack/datahub/commit/f7183374880fefdd1998120891cdcdb77f10f49e))
- Limit of 10k entries for filebased cache before culling ([ffc35ee](https://github.com/datasnack/datahub/commit/ffc35ee0f29d205c6b09763e4fbdbdb3ad73afdc))

## [0.8.2](https://github.com/datasnack/datahub/compare/v0.8.1..v0.8.2) - 2025-03-17

### Fixed

- Log view is paginated ([16c40bb](https://github.com/datasnack/datahub/commit/16c40bb1d311bdd1adb9f8baecef93fa7041eb6b))

## [0.8.1](https://github.com/datasnack/datahub/compare/v0.8.0..v0.8.1) - 2025-03-07

### Fixed

- Allow downloading csv and excel in DL shape list ([07a9a06](https://github.com/datasnack/datahub/commit/07a9a06870c597a81ea26a60d971fa5a1dc682ff))

## [0.8.0](https://github.com/datasnack/datahub/compare/v0.7.1..v0.8.0) - 2025-03-05

### Changed

- Bearer token based API access ([4874ae6](https://github.com/datasnack/datahub/commit/4874ae63c9d319cedd7ec3ae18404e9494b4ebfb))

### Fixed

- Show messages to the user if any ([e813687](https://github.com/datasnack/datahub/commit/e81368757dd4bf8dccbb2dc784527b77c0bf5fa8))
- De/serialization of SourceMetaData model ([9f49a04](https://github.com/datasnack/datahub/commit/9f49a04d058ab08d042bf747c9bfc1f460715e95))

## [0.7.1](https://github.com/datasnack/datahub/compare/v0.7.0..v0.7.1) - 2025-02-27

### Changed

- Admin action to copy metadata to n datalayers form 1 ([314540b](https://github.com/datasnack/datahub/commit/314540b3ba40a4d6267382a16b764f071d513b7f))

### Fixed

- Broken migration for setting key column on shape model ([faa6190](https://github.com/datasnack/datahub/commit/faa6190cc07ef19ed8c13c30e20bb0fff646d3b9))

## [0.7.0](https://github.com/datasnack/datahub/compare/v0.6.1..v0.7.0) - 2025-02-26

This updates contains a major restructuring of the Data Layer metadata resources. The existing metadata models are *not* migrated to the new format automatically.

### Changed

- New metadata model/form ([c3da789](https://github.com/datasnack/datahub/commit/c3da78910039e63f7eeff95a4ac471333f7459e1))
- Command to swap between different DH configs/instances ([a229449](https://github.com/datasnack/datahub/commit/a229449e413378a6e7f76270790965018275d646))

### Fixed

- Icon template helper trims whitespace ([534c4f6](https://github.com/datasnack/datahub/commit/534c4f69d82f0d6f24a9232f92e4cf54360fe645))
- Use data hub prefix for dump file name ([678f16e](https://github.com/datasnack/datahub/commit/678f16eb389a167f9e309dffe914c0102a7564eb))

## [0.6.1](https://github.com/datasnack/datahub/compare/v0.6.0..v0.6.1) - 2025-01-27

### Added

- Add description field to shape model ([7414ee0](https://github.com/datasnack/datahub/commit/7414ee0f3609606482ddcf8219da946f0373034b))

## [0.6.0](https://github.com/datasnack/datahub/compare/v0.5.2..v0.6.0) - 2025-01-23

### Changed

- Geometry attribution/license fields ([7a77ffd](https://github.com/datasnack/datahub/commit/7a77ffdf6df17fd0d5c336491fb69c470780f8e5))
- Utilize caching for API GeoJSON returns ([e8a38ba](https://github.com/datasnack/datahub/commit/e8a38ba580ed8c1cc7f3fcd4388edb77e014c697))
- Temporal resolution icon for Data Layers ([cf174f5](https://github.com/datasnack/datahub/commit/cf174f508f44fe47360dcc0a6c2da23787f83a40))
- Clear cache management command ([ac5d9cd](https://github.com/datasnack/datahub/commit/ac5d9cda8be4cf77319cf50c081c9e396c992b85))
- Simplify API response geometries per configuration ([8622a62](https://github.com/datasnack/datahub/commit/8622a62801d11d32e45b0737edd9aa76fc991333))

### Fixed

- Prefix instance key download names ([a5052dc](https://github.com/datasnack/datahub/commit/a5052dc4fd25e56e207c88925176a8222f8e3194))
- Dropdown overlapping base map selector in Leaflet ([385bf1e](https://github.com/datasnack/datahub/commit/385bf1e2f181cd03524010f00f5491741699a03c))

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
