from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_term_product = fields.Boolean('Term Product', default=False)
    landed_cost = fields.Float('Average Landed Cost')
