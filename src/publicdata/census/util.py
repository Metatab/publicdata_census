# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""

"""

def sub_geoids(v):
    """Replace state abbreviations and state fips codes with state and national geoids"""

    from geoid.censusnames import stusab
    from geoid.acs import Us, State, AcsGeoid

    if len(v) == 2:

        v = v.upper()

        stmap = { v:k for k,v in stusab.items() }

        if v == 'US':
            return str(Us())

        if v in stmap:
            return str(State(stmap[v]))

    # Maybe it is a state number
    try:
        v = int(v)
        return str(State(v))
    except ValueError:
        pass

    return str(AcsGeoid.parse(v))

def sub_summarylevel(v):
    """Replace summary level names with SL numbers"""

    from geoid.core import names

    try:
        int(v)
        return v
    except ValueError:
        return names[v.lower()]


def melt(df):
    """Melt a census dataframe into two value columns, for the estimate and margin"""
    import pandas as pd

    # Intial melt
    melted = pd.melt(df, id_vars=list(df.columns[:9]), value_vars=list(df.columns[9:]))
    melted = melted[['gvid', 'variable', 'value']]

    # Make two seperate frames for estimates and margins.
    estimates = melted[~melted.variable.str.contains('_m90')].set_index(['gvid', 'variable'])
    margins = melted[melted.variable.str.contains('_m90')].copy()

    margins.columns = ['gvid', 'ovariable', 'm90']
    margins['variable'] = margins.ovariable.str.replace('_m90', '')

    # Join the estimates to the margins.
    final = estimates.join(margins.set_index(['gvid', 'variable']).drop('ovariable', 1))

    return final


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.type(
    """
    import re
    import unicodedata
    from six import text_type
    value = text_type(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8')
    value = re.sub(r'[^\w\s-]', '-', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


CACHE_NAME = 'pandasreporter'


def nl2br(v, is_xhtml= True ):
    if is_xhtml:
        return v.replace('\n','<br />\n')
    else :
        return v.replace('\n','<br>\n')


# Cleaning universe strings. This is mostly for development
universe_strips = [
    'civilian','employed','noninstitutionalized','citizens','household','households','population',
    'full-time, year-round','foreign-born','nonfamily','families','family','workers','worked', 'born outside',
    'veterans', 'woman', 'women', 'female','man', 'men', 'male','vacant','occupied','owner-occupied','renter-occupied',
    'earnings','income'

]

def strip_age(v):
    from publicdata.census.files.text_filter import age_patterns
    for k, p in age_patterns.items():
        v = p.sub('',v)

    return v

def clean_universe(v):
    import re
    from publicdata.census.files.text_filter import ri_titles

    v = v.lower()
    for s in universe_strips:
        v = re.sub(r"\b"+s+r"\b",'', v)
    v = re.sub(ri_titles_p, '', v)
    v = strip_age(v)
    v = v.lower()
    v = re.sub('\s+',' ', v)
    v = v.strip(' ,')
    return v