# -*- coding: utf-8 -*-

from odoo import api, models, fields,_


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def print_picking(self):
        return self.env.ref('sale_report.action_report_stock_picking_sales')\
            .with_context(discard_logo_check=True).report_action(self)
