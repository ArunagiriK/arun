# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    barcode_new = fields.Char('Barcode')
    
    

class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_new = fields.Char(string='Barcode')
    
    @api.one
    @api.constrains('barcode_new')
    def _check_unique_barcode_new(self):
        if self.barcode_new:
            av_ids = []
            for av_obj in self.attribute_value_ids:
                if av_obj.is_custom:
                    av_ids.append(av_obj.id)
            print('av_ids : ', av_ids)
            flag = True
            for current_obj in self.search([('barcode_new', '=', self.barcode_new)]):
                if current_obj.id != self.id and self.barcode_new == current_obj.barcode_new:
                    new_av_ids = []
                    for old_av_obj in current_obj.attribute_value_ids:
                        if old_av_obj.is_custom:
                            new_av_ids.append(old_av_obj.id)
                    if av_ids != new_av_ids:
                        flag = False;break;
            if not flag:
                raise ValidationError("Barcode already exists for selected variants.")


            
        


