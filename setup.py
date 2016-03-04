from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'adecaptcha',
  ext_modules = cythonize("adecaptcha/pwrspec.pyx"),
)