"""Codes for table numbers and race iterations"""

from collections import namedtuple
from .dimensions import race_iterations

# Convert the race_iterations into a map
race_iter_map = { e[0]:e[1] for e in race_iterations}

table_prefixes = {
    'B': 'detailed',
    'C': 'collapsed',

}

table_subject_codes = {
    "00": 'Unweighted Count',
    "01": "Age and Sex",
    "02": "Race",
    "03": "Hispanic Origin",
    "04": "Ancestry",
    "05": "Foreign Born; Citizenship; Year or Entry; Nativity",
    "06": "Place of Birth",
    "07": "Residence 1 Year Ago; Migration",
    "08": "Journey to Work; Workers' Characteristics; Commuting",
    "09": "Children; Household Relationship",
    "10": "Grandparents; Grandchildren",
    "11": "Household Type; Family Type; Subfamilies",
    "12": "Marital Status and History",
    "13": "Fertility",
    "14": "School Enrollment",
    "15": "Educational Attainment",
    "16": "Language Spoken at Home and Ability to Speak English",
    "17": "Poverty",
    "18": "Disability",
    "19": "Income (Households and Families)",
    "20": "Earnings (Individuals)",
    "21": "Veteran Status",
    "22": "Transfer Programs (Public Assistance)",
    "23": "Employment Status; Work Experience; Labor Force",
    "24": "Industry; Occupation; Class of Worker",
    "25": "Housing Characteristics",
    "26": "Group Quarters",
    "27": "Health Insurance",
    "28": "Computer and Internet Use",
    "29": "Citizen Voting-age Population",
    '98': 'Quality Measures',
    '99': 'Imputations'
}

def describe_table(table_id: str) -> namedtuple:
    """Return a description of a table"""

    # Lookup the prefix and subject code
    prefix = table_prefixes[table_id[0].upper()]
    subject_code= table_id[1:3]
    subject = table_subject_codes[subject_code]

    # if the tables ends in a letter, it is a race iteration. Remove the letter
    # and lookup the associated race name
    if table_id[-1].isalpha():
        race_code = table_id[-1].upper()
        race_name = race_iter_map.get(race_code, 'Unknown')
        ti_root = table_id[:-1]
    else:
        race_name = 'all'
        ti_root = table_id

    table_number = table_id[3:]

    d = {
        'table_id': table_id,
        'ti_root': ti_root,
        'prefix': prefix,
        'subject': subject,
        'race': race_name,
        'technical': subject_code in ('00','98','99'),
    }

    # Return the description ind as a named tuple
    return namedtuple('TableDescription', d.keys())(*list(d.values()))
