from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup(
  name = 'adecaptcha',
  version='0.1',
  ext_modules = cythonize("adecaptcha/pwrspec.pyx"),
  include_dirs=[numpy.get_include()]
)
