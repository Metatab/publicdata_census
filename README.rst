=================
publicdata_census
=================


This library defines a set of `Application Urls
<https://github.com/CivicKnowledge/appurl>`_ and `Row Generators
<https://github.com/CivicKnowledge/rowgenerators>`_ that allow access to public
datasets. For instance, using the Census Reporter URLs, you can define access
to a American Community Survey data table on the Census Reporter website. Then,
using the associated Row Generator, you can download the data as a sequences of
rows.

For instance, this code will return rows from ACS table B17001 for tracts in San Diego County

.. code-block:: python

    from publicdata import  parse_app_url

    url = parse_app_url("census://CA/140/B17001")

    # Or: url = CensusReporterUrl(table='B17001',summarylevel='140',geoid='CA')

    for row in url.generator:
        print(row)


The library uses the appurl and rowgenerator python entrypoints, so all
libraries that you install that use the entrypoints can be accessed via the
``parse_app_url`` and ``get_generator`` functions.

Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
