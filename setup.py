from setuptools import setup, find_packages

setup(name='fam',
    version='1.0.7',
    description="Simple Python ORM for CouchDB, and Sync Gateway",
    url="https://github.com/paulharter/fam",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License'
    ],
    author='Paul Harter',
    author_email='username: paul, domain: glowinthedark.co.uk',
    license="LICENSE",
    install_requires=['requests', 'simplejson', 'jsonschema', 'mock', 'pytz'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False)

