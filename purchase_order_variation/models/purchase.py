# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
     _inherit = 'purchase.order'
    
     product_brand_id = fields.Many2one('product.brand', string='Brand')
     attribute_value_ids = fields.Many2many('product.attribute.value', string='Variants')
     product_information_purchase_line_ids = fields.One2many('product.information.line.purchase', 'purchase_id', string='Product Information')
     
     #~ product_information_ids = fields.Many2many('product.information.line',string='Product Information')
     
    
class PurchaseOrderLine(models.Model):
     _inherit = 'purchase.order.line'

     product_brand_id = fields.Many2one('product.brand', string='Brand')
     attribute_value_ids = fields.Many2many('product.attribute.value', string='Variants')
     brand = fields.Boolean('Brand')
        
     @api.model
     def default_get(self, fields):
        res = super(PurchaseOrderLine, self).default_get(fields)
        if 'parent_brand' in self.env.context and self.env.context['parent_brand'] == True:
            res['brand'] = True
            product_brand_id = self.env.context['product_brand_id']
            res['product_brand_id'] = product_brand_id
        return res
    
     @api.onchange('brand')
     def _onchange_brand(self):
        if self.brand:
           if 'product_brand_id' in self.env.context and self.env.context['product_brand_id'] == True:
               product_brand_id = self.env.context['product_brand_id']
               return {'domain': {'product_brand_id': [('id','=',product_brand_id)],'product_id':[('product_brand_id','=',product_brand_id)]}}
         
    
     @api.onchange('product_id', 'attribute_value_ids')
     def _onchange_variants(self):
         if self.product_id:
            self.attribute_value_ids = self.product_id.attribute_value_ids.ids
            
            
     
class ProductInformationLine(models.Model):
    _name = 'product.information.line.purchase'
    
    product_info_id = fields.Many2one('product.information', required=True, string='Information Type')
    name = fields.Char('Value', required=True)
    purchase_id = fields.Many2one('purchase.order', ondelete='cascade')
