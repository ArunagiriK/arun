# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one('product.brand', string='Brand')
    product_type_id  = fields.Many2one('product.style', string='Product style')


#~ class ProductProduct(models.Model):
    #~ _inherit = 'product.product'

    #~ product_brand_id = fields.Many2one('product.brand', string='Brand')
