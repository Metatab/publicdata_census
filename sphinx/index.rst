==================
Census Access Urls
==================


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

Contents
========

.. toctree::
   :maxdepth: 2

   General Use <census>
   Census Files <census_files>
   Census Reporter <census_reporter>
   Module Reference <api/modules>
   License <license>
   Authors <authors>
   Changelog <changelog>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _toctree: http://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _references: http://www.sphinx-doc.org/en/stable/markup/inline.html
.. _Python domain syntax: http://sphinx-doc.org/domains.html#the-python-domain
.. _Sphinx: http://www.sphinx-doc.org/
.. _Python: http://docs.python.org/
.. _Numpy: http://docs.scipy.org/doc/numpy
.. _SciPy: http://docs.scipy.org/doc/scipy/reference/
.. _matplotlib: https://matplotlib.org/contents.html#
.. _Pandas: http://pandas.pydata.org/pandas-docs/stable
.. _Scikit-Learn: http://scikit-learn.org/stable
.. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _Google style: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
.. _NumPy style: https://numpydoc.readthedocs.io/en/latest/format.html
.. _classical style: http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists
