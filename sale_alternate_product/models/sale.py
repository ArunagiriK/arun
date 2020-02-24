# -*- coding: utf-8 -*-

from odoo import api, models, fields,_


    
class SaleOrderLine(models.Model):
      _inherit = 'sale.order.line'
     
      product_existing_name = fields.Char('Product Existing Name',related='product_id.alternative_name',store=True)
    
      
    

class AccountInvoiceLine(models.Model):
      _inherit = 'account.invoice.line'

      product_existing_name = fields.Char('Product Existing Name',related='product_id.alternative_name',store=True)
