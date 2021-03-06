RandomGen
=========

Random Number Generator using settable Basic RNG interface for future
NumPy RandomState evolution.

**Continuous Integration**

|Travis Build Status| |Appveyor Build Status| |Build Status| |FreeBSD
Status on Cirrus|

**Coverage**

|Coverage Status| |codecov|

**Latest Release**

|PyPI version| |Anacnoda Cloud|

**License**

|NCSA License| |BSD License| |DOI|

This is a library and generic interface for alternative random
generators in Python and NumPy.

WARNINGS
========

Changes in v1.18
----------------

There are many changes between v1.16.x and v1.18.x. These reflect API
decision taken in conjunction with NumPy in preparation of the core of
``randomgen`` being used as the preferred random number generator in
NumPy. These all issue ``DeprecationWarning``\ s except for
``BasicRNG.generator`` which raises ``NotImplementedError``. The C-API
has also changed to reflect the preferred naming the underlying
Pseudo-RNGs, which are now known as bit generators (or
``BigGenerator``\ s).

Future Plans
------------

A substantial portion of randomgen has been merged into NumPy. Revamping
NumPy’s random number generation was always the goal of this project
(and its predecessor `NextGen NumPy
RandomState <https://github.com/bashtage/ng-numpy-randomstate%3E>`__),
and so it has succeeded.

While I have no immediate plans to remove anything, after a 1.19 release
I will:

-  Remove ``Generator`` and ``RandomState``. These duplicate NumPy and
   will diverge over time. The versions in NumPy are authoritative.
-  Preserve novel methods of ``Generator`` in a new class,
   ``ExtendedGenerator``.
-  Add some distributions that are not supported in NumPy.
-  Remove ``MT19937`` ``PCG64`` since these are duplicates of bit
   generators in NumPy.
-  Add any interesting bit generators I come across.

Python 2.7 Support
------------------

v1.16 is the final major version that supports Python 2.7. Any bugs in
v1.16 will be patched until the end of 2019. All future releases are
Python 3, with an initial minimum version of 3.5.

Compatibility Warning
---------------------

``Generator`` does not support Box-Muller normal variates and so it not
100% compatible with NumPy (or randomstate). Box-Muller normals are slow
to generate and all functions which previously relied on Box-Muller
normals now use the faster Ziggurat implementation. If you require
backward compatibility, a legacy generator, ``RandomState``, has been
created which can fully reproduce the sequence produced by NumPy.

Features
========

-  Designed as a peplacement for NumPy’s 1.16’s RandomState

   .. code:: python

      from randomgen import Generator, MT19937
      rnd = Generator(MT19937())
      x = rnd.standard_normal(100)
      y = rnd.random(100)
      z = rnd.randn(10,10)

-  Default random generator is a fast generator called Xoroshiro128plus
-  Support for random number generators that support independent streams
   and jumping ahead so that sub-streams can be generated
-  Faster random number generation, especially for normal, standard
   exponential and standard gamma using the Ziggurat method

   .. code:: python

      from randomgen import Generator
      # Default bit generator is Xoroshiro128
      rnd = Generator()
      w = rnd.standard_normal(10000)
      x = rnd.standard_exponential(10000)
      y = rnd.standard_gamma(5.5, 10000)

-  Support for 32-bit floating randoms for core generators. Currently
   supported:

   -  Uniforms (``random``)
   -  Exponentials (``standard_exponential``, both Inverse CDF and
      Ziggurat)
   -  Normals (``standard_normal``)
   -  Standard Gammas (via ``standard_gamma``)

   **WARNING**: The 32-bit generators are **experimental** and subject
   to change.

   **Note**: There are *no* plans to extend the alternative precision
   generation to all distributions.

-  Support for filling existing arrays using ``out`` keyword argument.
   Currently supported in (both 32- and 64-bit outputs)

   -  Uniforms (``random``)
   -  Exponentials (``standard_exponential``)
   -  Normals (``standard_normal``)
   -  Standard Gammas (via ``standard_gamma``)

-  Support for Lemire’s method of generating uniform integers on an
   arbitrary interval by setting ``use_masked=True``.

Included Pseudo Random Number Generators
----------------------------------------

This module includes a number of alternative random number generators in
addition to the MT19937 that is included in NumPy. The RNGs include:

-  Cryptographic cipher-based random number generator based on AES,
   ChaCha20, HC128 and Speck128.
-  `MT19937 <https://github.com/numpy/numpy/blob/master/numpy/random/mtrand/>`__,
   the NumPy rng
-  `dSFMT <http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/SFMT/>`__ a
   SSE2-aware version of the MT19937 generator that is especially fast
   at generating doubles
-  `xoroshiro128+ <http://xoroshiro.di.unimi.it/>`__,
   `xorshift1024*φ <http://xorshift.di.unimi.it/>`__,
   `xoshiro256*\* <http://xorshift.di.unimi.it/>`__, and
   `xoshiro512*\* <http://xorshift.di.unimi.it/>`__
-  `PCG64 <http://www.pcg-random.org/>`__
-  ThreeFry and Philox from
   `Random123 <https://www.deshawresearch.com/resources_random123.html>`__

Differences from ``numpy.random.RandomState``
---------------------------------------------

Note
~~~~

These comparrisons are relative to NumPy 1.16. The project has been
substantially merged into NumPy 1.17+.

New Features relative to NumPy 1.16
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``standard_normal``, ``normal``, ``randn`` and
   ``multivariate_normal`` all use the much faster (100%+) Ziggurat
   method.
-  ``standard_gamma`` and ``gamma`` both use the much faster Ziggurat
   method.
-  ``standard_exponential`` ``exponential`` both support an additional
   ``method`` keyword argument which can be ``inv`` or ``zig`` where
   ``inv`` corresponds to the current method using the inverse CDF and
   ``zig`` uses the much faster (100%+) Ziggurat method.
-  Core random number generators can produce either single precision
   (``np.float32``) or double precision (``np.float64``, the default)
   using the optional keyword argument ``dtype``
-  Core random number generators can fill existing arrays using the
   ``out`` keyword argument
-  Standardizes integer-values random values as int64 for all platforms.
-  ``randint`` supports generating using rejection sampling on masked
   values (the default) or Lemire’s method. Lemire’s method can be much
   faster when the required interval length is much smaller than the
   closes power of 2.

New Functions
~~~~~~~~~~~~~

-  ``random_entropy`` - Read from the system entropy provider, which is
   commonly used in cryptographic applications
-  ``random_raw`` - Direct access to the values produced by the
   underlying PRNG. The range of the values returned depends on the
   specifics of the PRNG implementation.
-  ``random_uintegers`` - unsigned integers, either 32-
   (``[0, 2**32-1]``) or 64-bit (``[0, 2**64-1]``)
-  ``jump`` - Jumps RNGs that support it. ``jump`` moves the state a
   great distance. *Only available if supported by the RNG.*
-  ``advance`` - Advanced the RNG ‘as-if’ a number of draws were made,
   without actually drawing the numbers. *Only available if supported by
   the RNG.*

Status
------

-  Builds and passes all tests on:

   -  Linux 32/64 bit, Python 2.7, 3.5, 3.6, 3.7
   -  Linux (ARM/ARM64), Python 3.7
   -  OSX 64-bit, Python 2.7, 3.5, 3.6, 3.7
   -  Windows 32/64 bit, Python 2.7, 3.5, 3.6, 3.7
   -  PC-BSD (FreeBSD) 64-bit, Python 2.7 *(Occasional, no CI)*

Version
-------

The package version matches the latest version of NumPy where
``RandomState(MT19937())`` passes all NumPy test.

Documentation
-------------

Documentation for the latest release is available on `my GitHub
pages <http://bashtage.github.io/randomgen/>`__. Documentation for the
latest commit (unreleased) is available under
`devel <http://bashtage.github.io/randomgen/devel/>`__.

Requirements
------------

Building requires:

-  Python (3.5, 3.6, 3.7, 3.8)
-  NumPy (1.13, 1.14, 1.15, 1.16, 1.17, 1.18)
-  Cython (0.26+)
-  tempita (0.5+), if not provided by Cython

Testing requires pytest (4.0+).

**Note:** it might work with other versions but only tested with these
versions.

Development and Testing
-----------------------

All development has been on 64-bit Linux, and it is regularly tested on
Travis-CI (Linux/OSX), Appveyor (Windows), Cirrus (FreeBSD) and Drone.io
(ARM/ARM64 Linux).

Tests are in place for all RNGs. The MT19937 is tested against NumPy’s
implementation for identical results. It also passes NumPy’s test suite
where still relevant.

Installing
----------

Either install from PyPi using

.. code:: bash

   pip install randomgen

or, if you want the latest version,

.. code:: bash

   pip install git+https://github.com/bashtage/randomgen.git

or from a cloned repo,

.. code:: bash

   python setup.py install

SSE2
~~~~

``dSFTM`` makes use of SSE2 by default. If you have a very old computer
or are building on non-x86, you can install using:

.. code:: bash

   python setup.py install --no-sse2

Windows
~~~~~~~

Either use a binary installer, or if building from scratch, use Python
3.6/3.7 with Visual Studio 2015/2017 Community Edition. It can also be
build using Microsoft Visual C++ Compiler for Python 2.7 and Python 2.7.

Using
-----

The separate generators are importable from ``randomgen``

.. code:: python

   from randomgen import Generator, ThreeFry, PCG64, MT19937
   rg = Generator(ThreeFry())
   rg.random(100)

   rg = Generator(PCG64())
   rg.random(100)

   # Identical to NumPy
   rg = Generator(MT19937())
   rg.random(100)

License
-------

Dual: BSD 3-Clause and NCSA, plus sub licenses for components.

Performance
-----------

Performance is promising, and even the mt19937 seems to be faster than
NumPy’s mt19937.

::

   Speed-up relative to NumPy (Uniform Doubles)
   ************************************************************
   DSFMT                 184.9%
   MT19937                17.3%
   PCG32                  83.3%
   PCG64                 108.3%
   Philox                 -4.9%
   ThreeFry              -12.0%
   Xoroshiro128          159.5%
   Xorshift1024          150.4%
   Xoshiro256            145.7%
   Xoshiro512            113.1%

   Speed-up relative to NumPy (64-bit unsigned integers)
   ************************************************************
   DSFMT                  17.4%
   MT19937                 7.8%
   PCG32                  60.3%
   PCG64                  73.5%
   Philox                -25.5%
   ThreeFry              -30.5%
   Xoroshiro128          124.0%
   Xorshift1024          109.4%
   Xoshiro256            100.3%
   Xoshiro512             63.5%

   Speed-up relative to NumPy (Standard normals)
   ************************************************************
   DSFMT                 183.0%
   MT19937               169.0%
   PCG32                 240.7%
   PCG64                 231.6%
   Philox                131.3%
   ThreeFry              118.3%
   Xoroshiro128          332.1%
   Xorshift1024          232.4%
   Xoshiro256            306.6%
   Xoshiro512            274.6%

.. |Travis Build Status| image:: https://travis-ci.org/bashtage/randomgen.svg?branch=master
   :target: https://travis-ci.org/bashtage/randomgen
.. |Appveyor Build Status| image:: https://ci.appveyor.com/api/projects/status/odc5c4ukhru5xicl/branch/master?svg=true
   :target: https://ci.appveyor.com/project/bashtage/randomgen/branch/master
.. |Build Status| image:: https://cloud.drone.io/api/badges/bashtage/randomgen/status.svg
   :target: https://cloud.drone.io/bashtage/randomgen
.. |FreeBSD Status on Cirrus| image:: https://api.cirrus-ci.com/github/bashtage/randomgen.svg
   :target: https://cirrus-ci.com/github/bashtage/randomgen
.. |Coverage Status| image:: https://coveralls.io/repos/github/bashtage/randomgen/badge.svg
   :target: https://coveralls.io/github/bashtage/randomgen
.. |codecov| image:: https://codecov.io/gh/bashtage/randomgen/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/bashtage/randomgen
.. |PyPI version| image:: https://badge.fury.io/py/randomgen.svg
   :target: https://pypi.org/project/randomgen/
.. |Anacnoda Cloud| image:: https://anaconda.org/bashtage/randomgen/badges/version.svg
   :target: https://anaconda.org/bashtage/randomgen
.. |NCSA License| image:: https://img.shields.io/badge/License-NCSA-blue.svg
   :target: https://opensource.org/licenses/NCSA
.. |BSD License| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-3-Clause
.. |DOI| image:: https://zenodo.org/badge/122181085.svg
   :target: https://zenodo.org/badge/latestdoi/122181085
