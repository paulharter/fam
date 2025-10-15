
from setuptools import setup, find_packages

setup(name='fam',
    version='4.0.1',
    description="Simple Python ORM for CouchDB, Firebase and Sync Gateway",
    url="https://github.com/paulharter/fam",
    classifiers=[
      'Development Status :: 4 - Beta',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 3.13',
      'License :: OSI Approved :: MIT License'
    ],
    author='Paul Harter',
    author_email='paul@glowinthedark.co.uk',
    license="LICENSE",
    install_requires=['requests', 'simplejson', 'jsonschema', 'mock', 'pytz',
                    'firebase_admin', 'grpcio'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False
)
