import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migración 3.13.0: (vacía — los cambios que estaban aquí se reubicaron en 3.14.0)."""
    _logger.info("Migración 3.13.0: sin cambios pendientes.")
