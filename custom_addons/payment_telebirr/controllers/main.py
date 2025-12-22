# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TelebirrController(http.Controller):
    _return_url = '/payment/telebirr/return'
    _notify_url = '/payment/telebirr/notify'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def telebirr_return_from_checkout(self, **data):
        """ Process the return from Telebirr after payment.
        
        :param dict data: The data returned by Telebirr
        """
        _logger.info("Handling return from Telebirr with data:\n%s", pprint.pformat(data))
        
        try:
            # Process the notification data
            request.env['payment.transaction'].sudo()._handle_notification_data('telebirr', data)
        except ValidationError:
            _logger.exception("Could not handle return from Telebirr")
        
        # Redirect to payment status page
        return request.redirect('/payment/status')

    @http.route(_notify_url, type='http', auth='public', methods=['POST'], csrf=False, save_session=False)
    def telebirr_webhook(self, **data):
        """ Process the notification from Telebirr.
        
        :param dict data: The notification data sent by Telebirr
        """
        _logger.info("Notification received from Telebirr with data:\n%s", pprint.pformat(data))
        
        try:
            # Process the notification data
            request.env['payment.transaction'].sudo()._handle_notification_data('telebirr', data)
        except ValidationError:
            _logger.exception("Could not handle notification from Telebirr")
            return 'FAIL'
        
        # Return success response
        return 'SUCCESS'
