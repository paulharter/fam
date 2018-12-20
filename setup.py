import os

import atexit
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install


def delete_old_slimit_files():
    """
    slimit generates two files with code generation lextab.py and yacctab.py
    slimit install ships with out of date versions of these files that have been created by ply 3.4
    To use ply 3.8 with slimit 0.8.1 you have to delete thses two files, they will be lazily recreated by slimit using the up to date ply
    """
    import site
    from importlib import reload
    reload(site)
    import sys
    def find_module_path():
        for p in sys.path:
            if os.path.isdir(p) and "slimit" in os.listdir(p):
                return os.path.join(p, "slimit")

    install_path = find_module_path()

    file_names = ["lextab.py", "yacctab.py"]
    for file_name in file_names:
        file_path = os.path.join(install_path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)


class PostDevelopCommand(develop, object):
    """Post-installation for development mode."""

    def __init__(self, *args, **kwargs):
        super(PostDevelopCommand, self).__init__(*args, **kwargs)
        def _post_install():
            delete_old_slimit_files()
        atexit.register(_post_install)


class PostInstallCommand(install, object):
    """Post-installation for installation mode."""

    def __init__(self, *args, **kwargs):
        super(PostInstallCommand, self).__init__(*args, **kwargs)
        def _post_install():
            delete_old_slimit_files()
        atexit.register(_post_install)


setup(name='fam',
    version='2.0.10',
    description="Simple Python ORM for CouchDB, and Sync Gateway",
    url="https://github.com/paulharter/fam",
    classifiers=[
      'Development Status :: 4 - Beta',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 3.6',
      'License :: OSI Approved :: MIT License'
    ],
    author='Paul Harter',
    author_email='paul@glowinthedark.co.uk',
    license="LICENSE",
    install_requires=['js2py', 'requests', 'simplejson', 'jsonschema', 'mock', 'pytz', 'slimit', 'ply==3.8',
                    'firebase_admin', 'six'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    cmdclass={
      'develop': PostDevelopCommand,
      'install': PostInstallCommand,
    }
)
