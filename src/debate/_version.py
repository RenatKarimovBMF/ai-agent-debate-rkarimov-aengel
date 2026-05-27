"""Single source of truth for the package version.

Per the course submission guidelines (V3, §8.1), the version starts at
1.00 for the first reviewable submission and is incremented on
meaningful changes. Configuration files declare the same version under
their top-level "version" key so the loader can validate that code and
config are in sync at startup.
"""

__version__ = "1.00"

EXPECTED_CONFIG_VERSION = __version__
