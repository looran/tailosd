from setuptools import setup

setup(name='watchme',
      version='0.1',
      description='Display system notifications on your desktop',
      url='http://github.com/looran/watchme',
      author='Laurent Ghigonis',
      author_email='laurent@gouloum.fr',
      license='BSD',
      packages=['watchme'],
      scripts=['bin/watchme'],
      zip_safe=False)
