# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning



class product_pricelist(models.Model):
    _inherit = "product.pricelist"
    od_discount = fields.Float(string="Discount")


class product_pricelist_item(models.Model):
    _inherit = "product.pricelist.item"
    od_description = fields.Char('Description')
    od_item_code = fields.Char('Item Code')
    od_article_no = fields.Char('Article#')
  
    
    @api.multi
    def odproduct_id_change(self, product):
        res = {}
        product_data = self.env['product.product'].browse(product)
        name = product_data.description_sale or product_data.description or product_data.name or ''
        return {'value':{'od_description':name}}
