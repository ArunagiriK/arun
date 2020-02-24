from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductStyle(models.Model):
    _name = 'product.style'

    name = fields.Char(string='Style Name', required=True)	
    code = fields.Char(string='Code',required=True)
