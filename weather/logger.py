"""Centralised logging configuration for the weather package.

Call ``setup_logging()`` once at application startup (e.g. in ``main.py``)
to apply a consistent format across every module that uses
``logging.getLogger(__name__)``.
"""

import logging


def setup_logging(verbose: bool = False) -> None:
    """Configure the root logger with a human-readable format.

    Parameters
    ----------
    verbose : bool, optional
        When *True* the level is set to ``DEBUG``; otherwise ``INFO``.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
