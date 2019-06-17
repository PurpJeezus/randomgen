import glob
import io
import os
from os.path import exists, getmtime, join, splitext
import platform
import struct
import sys

from Cython.Build import cythonize
import Cython.Compiler.Options
import numpy as np
from setuptools import Distribution, find_packages, setup
from setuptools.extension import Extension

import versioneer

try:
    import Cython.Tempita as tempita
except ImportError:
    try:
        import tempita
    except ImportError:
        raise ImportError('tempita required to install, '
                          'use pip install tempita')

try:
    import pypandoc

    # With an input file: it will infer the input format from the filename
    with open('README.rst', 'wb') as readme:
        readme.write(pypandoc.convert_file('README.md', 'rst').encode('utf8'))
except ImportError:
    import warnings

    warnings.warn(
        'Unable to import pypandoc.  Do not use this as a release build!')


with open('requirements.txt') as f:
    required = f.read().splitlines()

CYTHON_COVERAGE = os.environ.get('RANDOMGEN_CYTHON_COVERAGE', '0') in \
                  ('true', '1', 'True')
if CYTHON_COVERAGE:
    print('Building with coverage for cython modules, '
          'RANDOMGEN_CYTHON_COVERAGE=' +
          os.environ['RANDOMGEN_CYTHON_COVERAGE'])

LONG_DESCRIPTION = io.open('README.rst', encoding="utf-8").read()
Cython.Compiler.Options.annotate = True

# Make a guess as to whether SSE2 is present for now, TODO: Improve
INTEL_LIKE = any([val in k.lower() for k in platform.uname()
                  for val in ('x86', 'i686', 'i386', 'amd64')])
USE_SSE2 = INTEL_LIKE
print('Building with SSE?: {0}'.format(USE_SSE2))
if '--no-sse2' in sys.argv:
    USE_SSE2 = False
    sys.argv.remove('--no-sse2')

MOD_DIR = './randomgen'

DEBUG = False

EXTRA_INCLUDE_DIRS = []
EXTRA_LINK_ARGS = [] if os.name == 'nt' else []
EXTRA_LIBRARIES = ['m'] if os.name != 'nt' else []
# Undef for manylinux
EXTRA_COMPILE_ARGS = ['/Zp16'] if os.name == 'nt' else \
    ['-std=c99', '-U__GNUC_GNU_INLINE__']
if INTEL_LIKE and os.name != 'nt':
    EXTRA_COMPILE_ARGS += ['-maes']
if os.name == 'nt':
    EXTRA_LINK_ARGS = ['/LTCG', '/OPT:REF', 'Advapi32.lib', 'Kernel32.lib']
    if DEBUG:
        EXTRA_LINK_ARGS += ['-debug']
        EXTRA_COMPILE_ARGS += ["-Zi", "/Od"]
    if sys.version_info < (3, 0):
        EXTRA_INCLUDE_DIRS += [join(MOD_DIR, 'src', 'common')]

DEFS = [('NPY_NO_DEPRECATED_API', '0')]
# TODO: Enable once Cython >= 0.29
#  [('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]

if CYTHON_COVERAGE:
    DEFS.extend([('CYTHON_TRACE', '1'),
                 ('CYTHON_TRACE_NOGIL', '1')])

PCG64_DEFS = DEFS[:]
if sys.maxsize < 2 ** 32 or os.name == 'nt':
    # Force emulated mode here
    PCG64_DEFS += [('PCG_FORCE_EMULATED_128BIT_MATH', '1')]

DSFMT_DEFS = DEFS[:] + [('DSFMT_MEXP', '19937')]
SFMT_DEFS = DEFS[:] + [('SFMT_MEXP', '19937')]
AES_DEFS = DEFS[:]
CHACHA_DEFS = DEFS[:]
if USE_SSE2:
    if os.name == 'nt':
        EXTRA_COMPILE_ARGS += ['/wd4146', '/GL']
        if struct.calcsize('P') < 8:
            EXTRA_COMPILE_ARGS += ['/arch:SSE2']
    else:
        EXTRA_COMPILE_ARGS += ['-msse2', '-mssse3', '-mrdrnd']
    DSFMT_DEFS += [('HAVE_SSE2', '1')]
    SFMT_DEFS += [('HAVE_SSE2', '1')]
    if os.name != 'nt' or sys.version_info[:2] >= (3, 5):
        AES_DEFS += [('HAVE_SSE2', '1')]
        CHACHA_DEFS += [('__SSE2__', '1'), ('__SSSE3__', '1')]

files = glob.glob('./randomgen/*.in') + glob.glob('./randomgen/legacy/*.in')
for templated_file in files:
    output_file_name = splitext(templated_file)[0]
    if (exists(output_file_name) and
            (getmtime(templated_file) < getmtime(output_file_name))):
        continue
    with open(templated_file, 'r') as source_file:
        template = tempita.Template(source_file.read())
    with open(output_file_name, 'w') as output_file:
        output_file.write(template.substitute())

extensions = [Extension('randomgen.entropy',
                        sources=[join(MOD_DIR, 'entropy.pyx'),
                                 join(MOD_DIR, 'src', 'entropy', 'entropy.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'entropy')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.dsfmt",
                        ["randomgen/dsfmt.pyx",
                         join(MOD_DIR, 'src', 'dsfmt', 'dSFMT.c'),
                         join(MOD_DIR, 'src', 'dsfmt', 'dSFMT-jump.c'),
                         join(MOD_DIR, 'src', 'aligned_malloc',
                              'aligned_malloc.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'dsfmt')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DSFMT_DEFS,
                        ),
              Extension("randomgen.jsf",
                        ["randomgen/jsf.pyx",
                         join(MOD_DIR, 'src', 'jsf', 'jsf.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'jsf')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.sfmt",
                        ["randomgen/sfmt.pyx",
                         join(MOD_DIR, 'src', 'sfmt', 'sfmt.c'),
                         join(MOD_DIR, 'src', 'sfmt', 'sfmt-jump.c'),
                         join(MOD_DIR, 'src', 'aligned_malloc',
                              'aligned_malloc.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'sfmt')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=SFMT_DEFS,
                        ),
              Extension("randomgen.mt19937",
                        ["randomgen/mt19937.pyx",
                         join(MOD_DIR, 'src', 'mt19937', 'mt19937.c'),
                         join(MOD_DIR, 'src', 'mt19937', 'mt19937-jump.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'mt19937')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.mt64",
                        ["randomgen/mt64.pyx",
                         join(MOD_DIR, 'src', 'mt64', 'mt64.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'mt64')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.philox",
                        ["randomgen/philox.pyx",
                         join(MOD_DIR, 'src', 'philox', 'philox.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'philox')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS + [('R123_USE_PHILOX_64BIT', '1')]
                        ),
              Extension("randomgen.pcg64",
                        ["randomgen/pcg64.pyx",
                         join(MOD_DIR, 'src', 'pcg64', 'pcg64.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'pcg64')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        define_macros=PCG64_DEFS,
                        extra_link_args=EXTRA_LINK_ARGS
                        ),
              Extension("randomgen.pcg32",
                        ["randomgen/pcg32.pyx",
                         join(MOD_DIR, 'src', 'pcg32', 'pcg32.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'pcg32')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.threefry",
                        ["randomgen/threefry.pyx",
                         join(MOD_DIR, 'src', 'threefry', 'threefry.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'threefry')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.threefry32",
                        ["randomgen/threefry32.pyx",
                         join(MOD_DIR, 'src', 'threefry32', 'threefry32.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'threefry32')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.xoroshiro128",
                        ["randomgen/xoroshiro128.pyx",
                         join(MOD_DIR, 'src', 'xoroshiro128',
                              'xoroshiro128.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(
                                                               MOD_DIR, 'src',
                                                               'xoroshiro128')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.xorshift1024",
                        ["randomgen/xorshift1024.pyx",
                         join(MOD_DIR, 'src', 'xorshift1024',
                              'xorshift1024.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR, 'src',
                                                                'xorshift1024')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.xoshiro256",
                        ["randomgen/xoshiro256.pyx",
                         join(MOD_DIR, 'src', 'xoshiro256',
                              'xoshiro256.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(
                                                               MOD_DIR, 'src',
                                                               'xoshiro256')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.xoshiro512",
                        ["randomgen/xoshiro512.pyx",
                         join(MOD_DIR, 'src', 'xoshiro512',
                              'xoshiro512.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(
                                                               MOD_DIR, 'src',
                                                               'xoshiro512')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.rdrand",
                        ["randomgen/rdrand.pyx",
                         join(MOD_DIR, 'src', 'rdrand',
                              'rdrand.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(
                                                               MOD_DIR, 'src',
                                                               'rdrand')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.chacha",
                        ["randomgen/chacha.pyx",
                         join(MOD_DIR, 'src', 'chacha',
                              'chacha.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(
                                                               MOD_DIR, 'src',
                                                               'chacha')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=CHACHA_DEFS
                        ),

              Extension("randomgen.generator",
                        ["randomgen/generator.pyx",
                         join(MOD_DIR, 'src', 'distributions',
                              'distributions.c')],
                        libraries=EXTRA_LIBRARIES,
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include()],
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.common",
                        ["randomgen/common.pyx"],
                        libraries=EXTRA_LIBRARIES,
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include()],
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.bounded_integers",
                        ["randomgen/bounded_integers.pyx",
                         join(MOD_DIR, 'src', 'distributions',
                              'distributions.c')],
                        libraries=EXTRA_LIBRARIES,
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include()],
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS
                        ),
              Extension("randomgen.legacy.bounded_integers",
                        ["randomgen/legacy/bounded_integers.pyx",
                         join(MOD_DIR, 'src', 'legacy',
                              'legacy-distributions.c'),
                         join(MOD_DIR, 'src', 'distributions',
                              'distributions.c')],
                        libraries=EXTRA_LIBRARIES,
                        include_dirs=EXTRA_INCLUDE_DIRS +
                        [np.get_include()] + [join(MOD_DIR, 'legacy')],
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS + [('RANDOMGEN_LEGACY', '1')]
                        ),

              Extension("randomgen.mtrand",
                        ["randomgen/mtrand.pyx",
                         join(MOD_DIR, 'src', 'legacy',
                              'legacy-distributions.c'),
                         join(MOD_DIR, 'src', 'distributions',
                              'distributions.c')],
                        libraries=EXTRA_LIBRARIES,
                        include_dirs=EXTRA_INCLUDE_DIRS +
                        [np.get_include()] + [join(MOD_DIR, 'legacy')],
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=DEFS + [('RANDOMGEN_LEGACY', '1')]
                        ),
              Extension("randomgen.aes",
                        ["randomgen/aes.pyx",
                         join(MOD_DIR, 'src', 'aesctr', 'aesctr.c')],
                        include_dirs=EXTRA_INCLUDE_DIRS + [np.get_include(),
                                                           join(MOD_DIR,
                                                                'src',
                                                                'aesctr')],
                        libraries=EXTRA_LIBRARIES,
                        extra_compile_args=EXTRA_COMPILE_ARGS,
                        extra_link_args=EXTRA_LINK_ARGS,
                        define_macros=AES_DEFS
                        )
              ]

classifiers = ['Development Status :: 5 - Production/Stable',
               'Environment :: Console',
               'Intended Audience :: End Users/Desktop',
               'Intended Audience :: Financial and Insurance Industry',
               'Intended Audience :: Information Technology',
               'Intended Audience :: Science/Research',
               'License :: OSI Approved',
               'Operating System :: MacOS :: MacOS X',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: POSIX :: Linux',
               'Operating System :: Unix',
               'Programming Language :: C',
               'Programming Language :: Cython',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3.5',
               'Programming Language :: Python :: 3.6',
               'Programming Language :: Python :: 3.7',
               'Topic :: Adaptive Technologies',
               'Topic :: Artistic Software',
               'Topic :: Office/Business :: Financial',
               'Topic :: Scientific/Engineering',
               'Topic :: Security :: Cryptography']


class BinaryDistribution(Distribution):
    def is_pure(self):
        return False


setup(
    name='randomgen',
    version=versioneer.get_version(),
    classifiers=classifiers,
    cmdclass=versioneer.get_cmdclass(),
    ext_modules=cythonize(extensions,
                          compiler_directives={'language_level': '3',
                                               'linetrace': CYTHON_COVERAGE},
                          force=CYTHON_COVERAGE),
    packages=find_packages(),
    package_dir={'randomgen': './randomgen'},
    package_data={'': ['*.h', '*.pxi', '*.pyx', '*.pxd', '*.in'],
                  'randomgen.tests.data': ['*.csv']},
    include_package_data=True,
    license='NCSA',
    author='Kevin Sheppard',
    author_email='kevin.k.sheppard@gmail.com',
    distclass=BinaryDistribution,
    long_description=LONG_DESCRIPTION,
    description='Random generator supporting multiple PRNGs',
    url='https://github.com/bashtage/randomgen',
    keywords=['pseudo random numbers', 'PRNG', 'RNG', 'RandomState', 'random',
              'random numbers', 'parallel random numbers', 'PCG',
              'XorShift', 'dSFMT', 'MT19937', 'Random123', 'ThreeFry',
              'Philox'],
    zip_safe=False,
    install_requires=required
)
