"""
Direct access to Census ACS files, automatically downloaded from the Census website.
"""

from rowgenerators import parse_app_url
import logging

logger = logging.getLogger('publicdata.census.files')

from .appurl import CensusFileUrl


