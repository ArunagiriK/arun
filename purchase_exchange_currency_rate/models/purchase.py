# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from werkzeug.urls import url_encode

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    currency_rate = fields.Float('Currency USD ',digits=(0, 2),default = 1.0)
    currency_rate1 = fields.Float('Currency INR',digits=(0, 2))
    currency_rate2  = fields.Float('Currency AED',digits=(0, 2),default = 3.67)
    is_currency = fields.Boolean('Currency Exchange')
    
    @api.onchange('is_currency')
    def onchange_is_currency(self):
        if self.is_currency:
            self.currency_id = self.env['res.currency'].search([('name','=','USD')]).id
        else:
            self.currency_id = self.company_id.currency_id.id
    
    #~ currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES,
        #~ default=_get_field_name_default)

    #~ @api.multi
    #~ def _get_field_name_default(self):
    #~ currency_id = self.env['res.currency'].search([('name','=','USD')])
    #~ return currency_id
    
    #~ @api.multi
    #~ @api.onchange('currency_rate')
    #~ def currency_change_value(self):
        #~ if self.currency_rate:
           #~ currency_rate_inr = self.env['res.currency'].search([('name','=','INR')])
           #~ currency_rate_aed = self.env['res.currency'].search([('name','=','AED')])
           #~ self.currency_rate1 = (currency_rate_inr.rate * self.currency_rate)/self.currency_id.rate
           #~ self.currency_rate2 = (currency_rate_aed.rate * self.currency_rate)/self.currency_id.rate
    
    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        picking = self.env['stock.picking'].search([('purchase_id','=',self.id)])
        for rec in picking:
            if self.is_currency:
               rec.write({'is_currency': True})
        return res

    @api.multi
    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        currency_rate1_stock = self.env['stock.picking'].search([('origin','=',self.name)]).currency_rate1
        #~ for line in self.order_line:
            #~ line.price_subtotal = 
        #~ print('')
        action = self.env.ref('account.action_vendor_bill_template')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        # override the context to get rid of the default filtering
        result['context'] = {
            'type': 'in_invoice',
            'default_purchase_id': self.id,
            'default_currency_id': self.currency_id.id,
            'default_company_id': self.company_id.id,
            'company_id': self.company_id.id,
            'currency_rate1':currency_rate1_stock,
            
        }
        # choose the view_mode accordingly
        if len(self.invoice_ids) > 1 and not create_bill:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        else:
            res = self.env.ref('account.invoice_supplier_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            # Do not set an invoice_id if we want to create a new bill.
            if not create_bill:
                result['res_id'] = self.invoice_ids.id or False
        result['context']['default_origin'] = self.name
        result['context']['default_reference'] = self.partner_ref
        return result


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.currency_id:
            for line in self.invoice_line_ids.filtered(lambda r: r.purchase_line_id):
                date = self.date or self.date_invoice or fields.Date.today()
                company = self.company_id
                currency_rate1 = self.env.context.get('currency_rate1', False)
                price_unit = 0.0
                qty = 0
                if currency_rate1:
                    for x in line.purchase_id.order_line:
                       if x.product_id.id == line.product_id.id:
                          price_unit = x.price_unit
                          qty = x.product_qty
                    line.quantity = qty
                    line.price_unit =  (line.purchase_id.currency_rate1/currency_rate1) * price_unit
                else:
                    line.price_unit = line.purchase_id.currency_id._convert(
                    line.purchase_line_id.price_unit, self.currency_id, company, date, round=False)
                


