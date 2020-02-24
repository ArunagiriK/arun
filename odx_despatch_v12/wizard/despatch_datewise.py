# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp


class od_despatch_wizard_fields(models.Model):
	_name = "od.despatch.datewise"


	od_despatch_date = fields.Date(string="Despatch Date")
	od_despatch_ref_id = fields.Char(string="Despatch Ref")
	partner_id = fields.Many2one('res.partner', string='Partner')
	number = fields.Char(string='Invoice No')
	date_invoice = fields.Date(string='Invoice Date')
	amount_total = fields.Float(string='Invoice Amount')
	od_transport_type = fields.Selection([('own','Own Transportation'),('third','Third Party')],string="Despatch Type",default='own')
	od_transporter_id = fields.Many2one('res.partner', string='Transporter')
	od_trans_ref = fields.Char(string="Transporter Ref")
	no_ofcarton = fields.Float(string="No.of Carton")
	
	od_amount =  fields.Float(string="Amount")

