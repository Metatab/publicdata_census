
from .files.metafiles import TableMeta
from .appurl import CensusUrl
from .files.appurl import CensusFileUrl, CensusGeoUrl
from .censusreporter.url import CensusReporterUrl, CensusReporterShapeURL

from pkg_resources import get_distribution, DistributionNotFound

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'publicdata.census'
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound


def census_table(table, state, sl='state', year=2018, release=5):
    import rowgenerators as rg
    return rg.dataframe(f'census://{year}/{release}/{state}/{sl}/{table}')

def census_geo(state, sl='state', year=2018, release=5):
    import rowgenerators as rg
    return rg.geoframe(f'census://{year}/{release}/{state}/{sl}')