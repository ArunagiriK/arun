# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    is_currency = fields.Boolean('Currency Exchange')
    currency_rate = fields.Float('Currency USD ',digits=(0, 2))
    currency_rate1 = fields.Float('Currency INR',digits=(0, 2))
    currency_rate2  = fields.Float('Currency AED',digits=(0, 2))

    @api.onchange('currency_rate1')
    def currency_change_value_picking(self):
        if self.currency_rate1:
            purchase_id = self.env['purchase.order'].search([('name','=',self.origin)])
            self.currency_rate = (purchase_id.currency_rate1/self.currency_rate1)*purchase_id.amount_total
            self.currency_rate2 = ((purchase_id.currency_rate1 / self.currency_rate1)*purchase_id.amount_total) *purchase_id.currency_rate2



class StockMove(models.Model):
    _inherit = 'stock.move'


    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id):
        """ Overridden from stock_account to support amount_currency on valuation lines generated from po
        """
        
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id)
        if self.picking_id.currency_rate1 > 0:
                purchase_currency = self.purchase_line_id.currency_id
                purchase_price_unit = self.purchase_line_id.price_unit
                if self.picking_id.currency_rate1 > 0 and self.picking_id.purchase_id.currency_rate1 > 0 :
                    currency_move_valuation = (self.picking_id.purchase_id.currency_rate1/self.picking_id.currency_rate1) * purchase_price_unit 
                    rslt['credit_line_vals']['credit'] = currency_move_valuation * self.picking_id.purchase_id.currency_rate2
                    #~ rslt['credit_line_vals']['amount_currency'] = currency_move_valuation
                    rslt['debit_line_vals']['debit'] = currency_move_valuation * self.picking_id.purchase_id.currency_rate2
                    #~ rslt['debit_line_vals']['amount_currency'] =  -currency_move_valuation
        return rslt


    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            valuation_amount = cost

        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount)

        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value) and not self.env['ir.config_parameter'].sudo().get_param(
                'stock_account.allow_zero_cost'):
            raise UserError(_(
                "The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (
                            self.product_id.display_name,))
        credit_value = debit_value


        valuation_partner_id = self._get_partner_id_for_valuation_lines()
        amount = 0.0
        result = {}
        data = []
        if self.picking_id.currency_rate1 > 0:
            for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value,
                                                    debit_account_id, credit_account_id).values():
                print('=======================',line_vals['debit'],line_vals['credit'])
                if self.picking_id.currency_rate1 > 0 and self.picking_id.purchase_id.currency_rate1 > 0 :
                    amount = (self.picking_id.purchase_id.currency_rate1/self.picking_id.currency_rate1) * self.purchase_line_id.price_unit
                    data.append((0,0,{
                        'name':line_vals['name'],
                        'product_id':line_vals['product_id'],
                        'quantity':line_vals['quantity'],
                        'product_uom_id':line_vals['product_uom_id'],
                        'ref':line_vals['ref'],
                        'partner_id':line_vals['partner_id'],
                        'credit':line_vals['credit'],
                        'debit':line_vals['debit'],
                        'account_id':line_vals['account_id'],
                        'currency_id':line_vals['currency_id'],
                        'amount_currency':-amount if (line_vals['debit'] - line_vals['credit']) < 0 else amount,
                    }))

            res = data
            return res


        
    
      
