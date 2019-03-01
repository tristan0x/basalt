import os
import platform
import re
import subprocess
import sys

from setuptools import find_packages, setup, Extension
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        if platform.system() == "Windows":
            cmake_version = LooseVersion(
                re.search(r'version\s*([\d.]+)', out.decode()).group(1)
            )
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        extdir = os.path.join(extdir, ext.name)
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
            '-DPYTHON_EXECUTABLE=' + sys.executable,
            '-DBasalt_USE_pybind11:BOOL=True',
            '-DCMAKE_BUILD_TYPE=',
        ]

        optimize = 'ON' if self.debug else 'OFF'
        build_args = ['--config', optimize, '--target', '_basalt']

        if platform.system() == "Windows":
            cmake_args += [
                '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(
                    optimize.upper(), extdir
                )
            ]
            if sys.maxsize > 2 ** 32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DBasalt_CXX_OPTIMIZE:BOOL=' + optimize]
            build_args += ['--', '-j2']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get('CXXFLAGS', ''), self.distribution.get_version()
        )
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(
            ['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env
        )
        subprocess.check_call(
            ['cmake', '--build', '.'] + build_args, cwd=self.build_temp
        )


needs_sphinx = {'build_sphinx', 'upload_docs'}.intersection(sys.argv)
maybe_sphinx = ["sphinx==1.8.4", "exhale"] if needs_sphinx else []

setup(
    name='basalt',
    version='0.1.0',
    author='Blue Brain Project',
    author_email='bbp-ou-hpc@groupes.epfl.ch',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Programming Language :: C++',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Database :: Database Engines/Servers',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
    ],
    description='Graph DB Storage',
    long_description='',
    packages=['basalt', 'basalt.ngv'],
    ext_modules=[CMakeExtension('basalt')],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
    install_requires=[
        'cached-property>=1.5.1',
        'docopt>=0.6.2',
        'h5py>=2.7.1',
        'humanize>=0.5.1',
        'numpy>=1.13',
        'progress>=1.4',
    ],
    setup_requires=maybe_sphinx,
    entry_points="""
        [console_scripts]
        basalt-cli = basalt.cli:main
    """,
)
