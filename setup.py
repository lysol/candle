try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(name='candle',
  version='0.1',
  description='Candle',
  author='Derek Arnold',
  author_email='zzzzbest@gmail.com',
  url='http://github.com/lysol/candle',
  packages=['candle'],
  zip_safe=False,
  install_requires=[
      'psycopg2'
      ],
  include_package_data=True
)
