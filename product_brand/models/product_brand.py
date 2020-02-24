from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char(string='Brand Name', required=True)	
    code = fields.Char(string='Code',required=True)

    @api.constrains('name')
    def _check_brand_duplicate(self):
        for record in self:
            brand_names = self.search([('id','!=',self.id)]);
            for brand_name in brand_names:
                if str(brand_name.name).lower() == str(record.name).lower() and str(brand_name.code).lower() == str(record.code).lower():
                    raise ValidationError(_('Error ! Brand is already created.'))
