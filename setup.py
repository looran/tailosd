from setuptools import setup

setup(name='tailosd',
      version='0.1',
      description='Linux On Screen Display file tail',
      url='http://github.com/looran/tailosd',
      author='Laurent Ghigonis',
      author_email='laurent@gouloum.fr',
      license='BSD',
      package_dir={'tailosd': ''},
      packages=['tailosd'],
      scripts=['tailosd'],
      zip_safe=False)
