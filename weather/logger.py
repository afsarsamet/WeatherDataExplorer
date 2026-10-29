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
        When *True*, the ``weather`` loggers also show ``DEBUG`` messages.
        Third-party libraries (e.g. Matplotlib) always stay at ``INFO`` so
        their own debug output does not flood the terminal.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("weather").setLevel(
        logging.DEBUG if verbose else logging.INFO
    )
