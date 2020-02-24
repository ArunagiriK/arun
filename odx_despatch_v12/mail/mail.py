# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import dateutil
import email
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from collections import namedtuple
from email.message import Message
from email.utils import formataddr
from lxml import etree
from werkzeug import url_encode


from odoo import _, api, exceptions, fields, models, tools
from odoo.tools.safe_eval import safe_eval




class OrchidMailThread(models.AbstractModel):

    _inherit = 'mail.thread'

    @api.multi
    def message_post_with_view(self, views_or_xmlid, **kwargs):
        """ Helper method to send a mail / post a message using a view_id to
        render using the ir.qweb engine. This method is stand alone, because
        there is nothing in template and composer that allows to handle
        views in batch. This method should probably disappear when templates
        handle ir ui views. """
        values = kwargs.pop('values', None) or dict()
        try:
            from odoo.addons.website.models.website import slug
            values['slug'] = slug
        except ImportError:
            values['slug'] = lambda self: self.id
        if isinstance(views_or_xmlid, basestring):
            views = self.env.ref(views_or_xmlid, raise_if_not_found=False)
        else:
            views = views_or_xmlid
        if not views:
            return
        for record in self:
            values['object'] = record
            if record.state == 'draft' and ('sale.order' in str(record) or 'account.invoice' in str(record)):
                continue
            rendered_template = views.render(values, engine='ir.qweb')
            kwargs['body'] = rendered_template
            record.message_post_with_template(False, **kwargs)