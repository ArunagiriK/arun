# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2 import OperationalError

from odoo import api, fields, models, registry, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

import logging

_logger = logging.getLogger(__name__)

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'
    od_carton_no = fields.Char(string="Carton")
    od_packaging_no = fields.Char(string="Packaging")
    od_client_order_ref = fields.Char(string="Client Order Ref")
    od_incoterm = fields.Many2one('stock.incoterms',string="Incoterm")
    od_deliveryloc_id = fields.Many2one('od.delivery.loc',string='Delivery Location')
    od_requested_date = fields.Date(string="Requested Date") 
