# -*- encoding: utf-8 -*-

import time
import math

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.multi
    @api.depends('debit', 'credit', 'balance', 'tax_ids', 'move_id', 'company_id.currency_id')
    def _compute_tax_details(self):
        for mv_line in self:
            price_include_tax = 0.0
            price_exclude_tax = 0.0
            val = 0.0
            if not mv_line.tax_line_id:
                balance = abs(mv_line.balance)
                for c in mv_line.tax_ids.filtered(lambda tx: tx.price_include).with_context(exclude_price_include=True).compute_all(balance)['taxes']:
                    price_include_tax += c.get('amount', 0.0)
                total_amount = balance + price_include_tax
                for c in mv_line.tax_ids.filtered(lambda tx: not tx.price_include).compute_all(total_amount)['taxes']:
                    price_exclude_tax += c.get('amount', 0.0)
                val = price_include_tax + price_exclude_tax
            mv_line.tax_amount = val
            mv_line.tax_label = ", ".join(mv_line.tax_ids.mapped('name'))

    tax_amount = fields.Monetary(compute='_compute_tax_details', store=True, currency_field='company_currency_id',
        string='Tax', digits=dp.get_precision('Account'), readonly=True)
    tax_label = fields.Char(string='Tax Label', compute='_compute_tax_details', store=True, readonly=True)
    

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        context = dict(self._context or {})
        exclude_price_include = context.get('exclude_price_include', False)
        if exclude_price_include and self.amount_type in ['percent', 'division'] and self.price_include:
            if self.amount_type == 'percent':
                return base_amount * self.amount / 100        
            elif self.amount_type == 'division':
                return base_amount / (1 - self.amount / 100) - base_amount        
        else:
            return super(AccountTax, self)._compute_amount(base_amount=base_amount, price_unit=price_unit, quantity=quantity, product=product, partner=partner)
