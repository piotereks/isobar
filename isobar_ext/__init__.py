"""
isobar_ext
~~~~~~

A Python library for algorithmic composition by expressing and constructing musical patterns.

For documentation, please see:

    https://github.com/piotereks/isobar-ext

For a full list of all Pattern classes:

    pydoc3 isobar_ext.pattern

"""

# flake8: noqa

__version__ = "0"
__author__ = "Daniel Jones <http://www.erase.net/>"

from .chord import *
from .constants import *
from .exceptions import *
from .io import *
from .key import *
from .note import *
from .pattern import *
from .scale import *
from .timelines import *
from .util import *
