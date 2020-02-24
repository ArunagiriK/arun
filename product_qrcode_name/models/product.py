# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.osv import expression
import re

class ProductCategory(models.Model):
    _inherit = 'product.category'

    qr_value = fields.Boolean('QR Value')
    code =fields.Char('Category Code')

class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"
    
    code = fields.Char('Code')
    
    @api.multi
    def name_get(self):
        if not self._context.get('show_attribute', True):  # TDE FIXME: not used
            return super(ProductAttributeValue, self).name_get()
        return [(value.id, "%s: %s: %s" % (value.attribute_id.name, value.name ,value.code)) for value in self]
    
    @api.multi
    def _variant_name(self, variable_attributes):
        return ", ".join([v.name for v in self if v.attribute_id in variable_attributes])
    
class product_product(models.Model):
    _inherit = 'product.product'
    
    #~ product_brand_id = fields.Many2one('product.brand','Brand')
    
    

    def get_category_value(self, category_obj):
        if category_obj.qr_value:
            return category_obj.code[:2]
        else:
            return None
    
    @api.onchange('product_brand_id','product_type_id','categ_id','attribute_value_ids')
    def _onchange_product_brand_id(self):
        if self.product_brand_id or self.categ_id or self.attribute_value_ids:
            qr_code = ''
            if self.product_brand_id.code:
                qr_code += self.product_brand_id.code[:2]
                qr_code += '-'
            if self.product_type_id.code:
               qr_code += self.product_type_id.code
            if self.categ_id.code:
                qr_code += '-'
                if not self.categ_id.parent_id:
                    qr_code += self.categ_id.code[:2]
                else:
                    category_value = []
                    if self.categ_id.qr_value:
                        #qr_code += self.categ_id.name[:2]
                        category_value.append(self.categ_id.code[:2])
                        
                    flag = True
                    category_obj = self.categ_id.parent_id
                    while flag:
                        value = self.get_category_value(category_obj)
                        if value:
                            #category_value += value
                            category_value.append(value)
                        if category_obj.parent_id:
                            category_obj = category_obj.parent_id
                        else:
                            flag = False
                    category_value.reverse()
                    for ca in category_value:
                        qr_code += ca
                        qr_code += '-'
                    #qr_code += category_value
            if self.attribute_value_ids:
                #~ qr_code += '-'
                for att in self.attribute_value_ids:
                    qr_code += str(att.code)
                    qr_code += '-'
            if qr_code[-1:] == '-':
                qr_code = qr_code[:-1]
            self.qr_code = qr_code

class ProductTemplate(models.Model):
    _inherit ='product.template' 

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        for variant in res.product_variant_ids:
            variant._onchange_product_brand_id()
        return res
    
    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        print(vals)
        for variant in self.product_variant_ids:
            variant._onchange_product_brand_id()
        return res
