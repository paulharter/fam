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

    import slimit
    file_names = ["lextab.py", "yacctab.py"]
    dir = os.path.dirname(slimit.__file__)
    for file_name in file_names:
        file_path = os.path.join(dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        def _post_install():
            delete_old_slimit_files()
        atexit.register(_post_install)



class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        def _post_install():
            delete_old_slimit_files()
        atexit.register(_post_install)



setup(name='fam',
    version='2.0.0',
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
    install_requires=['js2py', 'requests', 'simplejson', 'jsonschema', 'mock', 'pytz', 'slimit', 'ply',
                    'firebase_admin'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    cmdclass={
      'develop': PostDevelopCommand,
      'install': PostInstallCommand,
    }
)
