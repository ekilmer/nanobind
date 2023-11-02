import os
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

# Allow the user to specify whether nanobind Python package includes
# submodule'd dependency(s).
# Must be set to a CMake boolean value
NB_USE_SUBMODULE_DEPS = os.environ.get("NB_USE_SUBMODULE_DEPS", "ON")

VERSION_REGEX = re.compile(
    r"^\s*#\s*define\s+NB_VERSION_([A-Z]+)\s+(.*)$", re.MULTILINE)

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, "include/nanobind/nanobind.h")) as f:
    matches = dict(VERSION_REGEX.findall(f.read()))
    nanobind_version = "{MAJOR}.{MINOR}.{PATCH}".format(**matches)

long_description = '''
![nanobind logo](
https://github.com/wjakob/nanobind/raw/master/docs/images/logo.jpg?raw=True)

_nanobind_ is a small binding library that exposes C++ types in Python and
vice versa. It is reminiscent of
[Boost.Python](https://www.boost.org/doc/libs/1_64_0/libs/python/doc/html)
and [pybind11](http://github.com/pybind/pybind11) and uses near-identical
syntax. In contrast to these existing tools, nanobind is more efficient:
bindings compile in a shorter amount of time, produce smaller binaries, and
have better runtime performance.

More concretely,
[benchmarks](https://nanobind.readthedocs.io/en/latest/benchmark.html) show up
to **~4× faster** compile time, **~5× smaller** binaries, and **~10× lower**
runtime overheads compared to pybind11. nanobind also outperforms Cython in
important metrics (**3-12×** binary size reduction, **1.6-4×** compilation time
reduction, similar runtime performance).

Please see the following links for tutorial and reference documentation in
[HTML](https://nanobind.readthedocs.io/en/latest/) and
[PDF](https://nanobind.readthedocs.io/_/downloads/en/latest/pdf/) formats.
'''

tmp_install_dir = TemporaryDirectory(prefix="nanobind_cmake_")
install_dir = tmp_install_dir.name


class NanobindSdistCommand(sdist):
    def run(self):
        # Reset the package directory to the current directory for generating
        # sdist, or else the temporary installation directory has nothing
        self.distribution.package_dir['nanobind'] = os.curdir
        return super().run()


class NanobindBuildPyCommand(build_py):
    def run(self):
        cmake_exe = shutil.which("cmake")
        if not cmake_exe:
            print("CMake executable can't be found", file=sys.stderr)
            exit(1)

        with TemporaryDirectory() as build_dir:
            # Configure
            # TODO: Include robin_map based on env variable
            subprocess.check_call(
                [
                    cmake_exe,
                    "-S", this_directory,
                    "-B", build_dir,
                    "-DNB_PYTHON_INSTALLATION=ON",
                    f"-DNB_USE_SUBMODULE_DEPS={NB_USE_SUBMODULE_DEPS}",
                ],
                stdout=sys.stderr
            )
            # Install
            subprocess.check_call(
                [cmake_exe, "--install", build_dir, "--prefix", install_dir],
                stdout=sys.stderr
            )

        return super().run()


setup(
    name="nanobind",
    version=nanobind_version,
    author="Wenzel Jakob",
    author_email="wenzel.jakob@epfl.ch",
    description='nanobind: tiny and efficient C++/Python bindings',
    url="https://github.com/wjakob/nanobind",
    license="BSD",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['nanobind'],
    zip_safe=False,
    package_dir={'nanobind': install_dir},
    package_data={'nanobind': [
        'include/nanobind/**/*.h',
        'include/nanobind/intrusive/*.inl',
        '**/cmake/nanobind-config.cmake',
        '**/cmake/nanobind.cmake',
        '**/cmake/darwin-ld-cpython.sym',
        '**/cmake/darwin-ld-pypy.sym',
        'src/**/*.h',
        'src/**/*.cpp',
        'src/**/*.py',
        '**/ext/robin_map/include/tsl/*.h',
        '**/ext/robin_map/*.natvis',
        '**/ext/robin_map/CMakeLists.txt',
        'CMakeLists.txt',
        'nanobind-config.cmake.in',
        'tests/*.h',
        'tests/*.cpp',
    ]},
    cmdclass={
        'build_py': NanobindBuildPyCommand,
        'sdist': NanobindSdistCommand,
    }
)
