from odoo import models,fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    substitute_product_ids = fields.Many2many(comodel_name='product.product', relation='substitute_product_rel',
                                              column1='product_id', column2='substitute_id',
                                              string='Substitute Products')
