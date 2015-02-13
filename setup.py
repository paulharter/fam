from setuptools import setup, find_packages

setup(name='fam',
    version='0.1',
    description=’Simple Python relational ORM for CouchDB and Couchbase’,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7.6',
        'License :: MIT'
    ],
    author='Paul Harter',
    author_email='username: paul, domain: glowinthedark.co.uk',
    install_requires=['requests'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False)

