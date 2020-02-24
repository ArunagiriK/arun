from odoo import models, api, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_ids = fields.Many2many(comodel_name='res.company', relation='product_template_company_rel',
                                   column1='product_template_id', column2='company_id', string='Company')

class ProductCategory(models.Model):
    _inherit = 'product.category'

    company_ids = fields.Many2many(comodel_name='res.company', relation='product_category_company_rel',
                                   column1='product_category_id', column2='company_id', string='Company')