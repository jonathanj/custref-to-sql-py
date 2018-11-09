import os
import codecs
import versioneer
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    name='custref-to-sql',
    description='Python tool to convert proprietary customer reference data to SQL.',
    license='MIT',
    url='https://github.com/jonathanj/custref-to-sql-py',
    author='Jonathan Jacobs',
    author_email='jonathan@codeherent.io',
    maintainer='Jonathan Jacobs',
    maintainer_email='jonathan@codeherent.io',
    long_description=read('README.rst'),
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points = {
        'console_scripts': ['custref-to-sql=custref_to_sql.main:main'],
    },
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Utilities',
    ],
)
