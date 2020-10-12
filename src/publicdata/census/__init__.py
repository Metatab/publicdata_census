
from .files.metafiles import TableMeta
from .appurl import CensusUrl
from .files.appurl import CensusFileUrl, CensusGeoUrl
from .censusreporter.url import CensusReporterUrl, CensusReporterShapeURL

def census_table(table, state, sl='state', year=2018, release=5):
    import rowgenerators as rg
    return rg.dataframe(f'census://{year}/{release}/{state}/{sl}/{table}')

def census_geo(state, sl='state', year=2018, release=5):
    import rowgenerators as rg
    return rg.geoframe(f'census://{year}/{release}/{state}/{sl}')