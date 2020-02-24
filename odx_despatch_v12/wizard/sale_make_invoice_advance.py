# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

 
    @api.multi
    def _create_invoice(self, order, so_line, amount):
        od_deliveryloc_id = order.od_deliveryloc_id and order.od_deliveryloc_id.id
        od_requested_date = order.requested_date
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        invoice.od_deliveryloc_id = od_deliveryloc_id
        invoice.od_requested_date = od_requested_date
        
        return invoice

  
