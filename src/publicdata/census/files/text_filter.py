import re

from publicdata.census.dimensions import race_iterations

# Remove the path items ( col 1 ) and set the field ( col 2 ) to the value (col_3

path_filter = [
    ('naturalized u.s. citizen', 'citizen', 'Y'),
    ('not a u.s. citizen', 'citizen', 'N'),
    ('employed', 'employed', 'Y'),
    ('worked in the past 12 months', 'employed', 'Y'),
    ('unemployed', 'employed', 'N'),
    ('worked full-time, year-round in the past 12 months', 'employed', 'Y'),
    ('in labor force', 'employed', 'Y'),
    ('not in labor force', 'employed', 'N'),
    ('other family', 'family', 'family'),
    ('in family households', 'family', 'family'),
    ('foreign born', 'foreign_born', 'Y'),
    ('native', 'foreign_born', 'N'),
    ('group quarters population', 'group_quarters', 'group_quarters'),
    ('juvenile facilities', 'group_quarters', 'juvenile'),
    ('nursing facilities|skilled nursing facilities', 'group_quarters', 'nursing'),
    ('adult correctional facilities', 'group_quarters', 'correctional'),
    ('military quarters|military ships', 'group_quarters', 'military'),
    ('noninstitutionalized group quarters population', 'group_quarters', 'noninstitutionalized'),
    ('institutionalized group quarters population', 'group_quarters', 'institutionalized'),
    ('college|university student housing', 'group_quarters', 'college'),
    ('with income', 'has_income', 'Y'),
    ('with earnings', 'has_income', 'Y'),
    ('now married, except separated', 'marital_status', 'married'),
    ('married, spouse present', 'marital_status', 'married'),
    ('now married (including separated and spouse absent)', 'marital_status', 'married'),
    ('now married', 'marital_status', 'married'),
    ('widowed', 'marital_status', 'widowed'),
    ('divorced', 'marital_status', 'divorced'),
    ('married, spouse absent', 'marital_status', 'married'),
    ('never married', 'marital_status', 'never'),
    ('separated', 'marital_status', 'separated'),
    ('married-couple family', 'marital_status', 'married'),
    ('owner occupied', 'tenure', 'owner'),
    ('2.00 to 3.99 of poverty threshold', 'poverty_status', '200-400'),
    ('1.38 to 1.99 of poverty threshold', 'poverty_status', '138-200'),
    ('1.00 to 1.37 of poverty threshold', 'poverty_status', '100-138'),
    ('under 1.00 of poverty threshold', 'poverty_status', 'lt100'),
    ('4.00 of poverty threshold and over', 'poverty_status', 'gt400'),
    ('income in the past 12 months below the poverty level', 'poverty_status', 'gt100'),
    ('income in the past 12 months at or above the poverty level', 'poverty_status', 'gt100'),
    ('income in the past 12-months at or above poverty level', 'poverty_status', 'gt100'),
    ('income in the past 12-months below poverty level', 'poverty_status', 'lt100'),
    ('below 100 percent of the poverty level', 'poverty_status', 'lt100'),
    ('at or above 150 percent of the poverty level', 'poverty_status', 'gt150'),
    ('income in the past 12 months below poverty level', 'poverty_status', 'lt100'),
    ('100 to 149 percent of the poverty level', 'poverty_status', '100-150'),
    ('income in the past 12 months at or above poverty level', 'poverty_status', 'gt100'),
    ('renter occupied', 'tenure', 'renter')]

universe_filter = [

    ('not living in a metropolitan or micropolitan statistical area', 'msa', 'non_msa'),
    ('in a Micropolitan Statistical Area', 'msa', 'micropolitan'),
    ('in a Metropolitan Statistical Area', 'msa', 'metropolitan'),

    ('civilians?', 'military', 'civilian'),
    ('veterans?', 'military', 'veteran'),

    ('foreign born', 'foreign_born', 'Y'),
    ('born outside', 'foreign_born', 'Y'),
    ('foreign-born', 'foreign_born', 'Y'),

    ('employed', 'employed', 'Y'),
    ('work(ers|er)', 'employed', 'Y'),
    ('who worked', 'employed', 'Y'),
    ('who have worked', 'employed', 'Y'),

    ('with earnings', 'has_income', 'Y'),
    ('earnings', 'has_income', 'Y'),
    ('with income', 'has_income', 'Y'),
    ('full-time', 'ft_employed', 'Y'),

    ('grand(parents|parent|children|child)', 'grand_pc', 'Y'),

    ('occupied', 'tenure', 'occupied'),
    ('renter(-occupied)?', 'tenure', 'renter'),
    ('owner(-occupied)', 'tenure', 'owner'),
    ('vacant', 'tenure', 'vacant'),

    ('household(s|er)?', 'household', 'Y'),

    ('nonfamily|nonfamilies', 'family', 'nonfamily'),
    ('subfamily|subfamilies', 'family', 'subfamily'),
    ('family|families', 'family', 'family'),
    ('Unrelated individuals', 'family', 'unrelated'),

    ('below the poverty level', 'poverty_status', 'lt100'),

    ('group quarters', 'group_quarters', 'group_quarters'),
    ('noninstitutionalized', 'group_quarters', 'noninstitutionalized'),
    ('institutionalized', 'group_quarters', 'institutionalized'),

    ('opposite-sex', 'opposite_sex', 'Y'),
    ('married(-couple)', 'marital_status', 'married'),
    ('housing units', 'housing', 'Y'),


    ('enrolled in school', 'education', 'enrolled'),
    ("BACHELOR'S DEGREE OR HIGHER ATTAINMENT", 'education', 'bachelors+'),


]

strip_phrases = (
    r'Sex By Age By',
    r'By Sex By Age',
    r'Sex By Age',
    r'Sex By',
    r'Age By',
    r'In The Past 12 Months',
    r'\(In 2020 Inflation-Adjusted Dollars\)',
    r'\(Dollars\)',
    r'\(3 Types\)',
    r'\(5 Types\)',
    r'For The Full-Time, Year-Round Civilian Employed Population 16 Years And Over',
    r'For The Full-Time, Year-Round Civilian Employed Male Population 16 Years And OverFor The Full-Time, Year-Round Civilian Employed Female Population 16 Years And Over',
    r'\bwomen\b',
    r'\bmen\b',
    r'\bmale\b',
    r'\bfemale\b',
    r'\bfemales\b',
    r'people who are',
    r'or in combination with one or more other races',
    r'Puerto Rico',
    r'the United States',
    r'for whom poverty status is determined',
    r'total',
    r'year-round',
    r'population',
    r'with a',
    r'who is',
    r'who did not work from home',
    r'living with own',
    r'under 18 living with',
    r'paying cash rent',
    r'living',
    #r'Own children',
    r'in in',
    r'in and',
    r'excluding born at sea',
    r',',
    r'^Or$',
    r'\sIn$'
    r'\(\)',
    r'\)$',
    r'\(Aian\) Alone Or',
)

#

def clean_universe(universe):
    import re

    universe = universe.replace(',','')

    universe = re.sub(ri_titles_p, '', universe)

    for p in age_patterns.values():
        universe = re.sub(p, '', universe)

    universe = re.sub(r'\s+', ' ', universe)

    for phrase in tuple([e[0] for e in universe_filter]):
        universe = re.sub(r'\b' + phrase + r'\b', '', universe, flags=re.IGNORECASE)

    for pattern in strip_phrases:
        universe = re.sub(pattern, '', universe, flags=re.IGNORECASE)

    universe = re.sub(r'\s+', ' ', universe)

    if universe.strip() in ('in','in and', 'in in'):
        return ''

    return universe.strip()


def universe_flags(universe):
    from .text_filter import universe_filter
    import re

    universe = universe.lower()

    if not universe.strip():
        return None

    flags = {}
    for e, var, val in universe_filter:
        flags[var] = None

    for phrase, var, val in universe_filter:
        if re.search(r'\b' + phrase + r'\b', universe):
            flags[var] = val

    return flags


ri_code_map = {code.lower(): race for code, race, term in race_iterations if code}
ri_titles = []

# A regex to remove race interations from the table titles
for _, _, ri in race_iterations:
    ri_titles.append(fr"\(?{ri} Alone Householder\)?".title())
    ri_titles.append(fr"\(?{ri} Householder\)?".title())
    ri_titles.append(fr"\(?{ri} Alone\)?".title())
    ri_titles.append(fr"\(?{ri}\)?".title())

ri_titles.append(fr"\(?American Indian (?:and|or) Alaskan? Native(?: alone)?\)?".title())

ri_titles.append(fr"\(?AIAN alone or in any combination\)?".title())


ri_titles_p = re.compile('|'.join(ri_titles), re.IGNORECASE)
age_patterns = {
    'to': re.compile("(?P<lower>\d+) to (?P<upper>\d+) years", re.IGNORECASE),
    'and': re.compile("(?P<lower>\d+) and (?P<upper>\d+) years", re.IGNORECASE),
    'under': re.compile("under (?P<upper>\d+) years", re.IGNORECASE),
    'over': re.compile("(?P<lower>\d+) years? and over", re.IGNORECASE),
    'single': re.compile("(?P<upperlower>\d+) years", re.IGNORECASE),

}
