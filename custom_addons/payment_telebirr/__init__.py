# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from . import controllers

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Post-installation hook to set up Telebirr payment provider."""
    _logger.info('Telebirr payment provider installed successfully')


def uninstall_hook(env):
    """Pre-uninstallation hook to clean up Telebirr data."""
    _logger.info('Telebirr payment provider uninstalled')
