# -*- coding: utf-8 -*-
from odoo import models, api, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    article_no = fields.Char(string='Article Number')
    

#~ class ProductProduct(models.Model):
    #~ _inherit = 'product.product'
    
    #~ article_no = fields.Char(string='Article Number')
