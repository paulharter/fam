
from setuptools import setup, find_packages

setup(name='fam',
    version='2.2.7',
    description="Simple Python ORM for CouchDB, Firebase and Sync Gateway",
    url="https://github.com/paulharter/fam",
    classifiers=[
      'Development Status :: 4 - Beta',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 3.7',
      'License :: OSI Approved :: MIT License'
    ],
    author='Paul Harter',
    author_email='paul@glowinthedark.co.uk',
    license="LICENSE",
    install_requires=['js2py', 'requests', 'simplejson', 'jsonschema', 'mock', 'pytz', 'slimit', 'ply==3.4',
                    'firebase_admin', 'six', 'grpcio'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False
)
