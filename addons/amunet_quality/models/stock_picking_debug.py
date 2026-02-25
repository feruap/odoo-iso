
import logging

_logger = logging.getLogger(__name__)

def debug_context(env_context, vals):
    _logger.info("="*50)
    _logger.info("DEBUG: stock.picking.create called")
    _logger.info(f"VALS: {vals}")
    _logger.info(f"CONTEXT: {env_context}")
    _logger.info("="*50)
