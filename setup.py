from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'adecaptcha',
  version='0.1',
  ext_modules = cythonize("adecaptcha/pwrspec.pyx"),
)