from odoo import models,fields,api

class ProductInformation(models.Model):
    _name = 'product.information'

    name = fields.Char(string='Information Type')



