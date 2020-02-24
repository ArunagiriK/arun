# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.addons.stock_landed_costs.models import product
from odoo.exceptions import UserError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    @api.multi
    def button_validate(self):
        res = super(LandedCost, self).button_validate()
        for cost in self:
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                if line.product_id.qty_available > 0:
                    line.product_id.average_landed_cost = line.product_id.stock_value / line.product_id.qty_available
        return res
