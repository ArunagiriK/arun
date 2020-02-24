# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Codeware Computiung LLC (<http://www.codewareuae.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import models, fields, api, _

class add_tax(models.TransientModel):
    _name = 'add.tax'

    product_ids = fields.Many2many('product.template', 'product_temp_tax_wiz', 'pro_id', 'wiz_id', string='Products', domain="[('company_id', '=', company_id)]", help="Select no of products. If no products selected applied to all the products!")
    customer_tax = fields.Boolean('Customer Tax', default=True)
    supplier_tax = fields.Boolean('Supplier Tax', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    
    
    @api.multi
    def apply_tax(self):
        product_obj = self.env['product.template']
        company_id = self.company_id.id
        country_module = 'l10n_ae'        
        sale_tax_temp = str(company_id)+'_sale_tax_template'
        sale_tax_ref =  '.'.join([country_module, sale_tax_temp])
        sale_tax_account = self.env.ref(sale_tax_ref, False)
        purchase_tax_temp = company_id+'_purchase_tax_template'
        purchase_tax_ref =  '.'.join([country_module, purchase_tax_temp])
        purchase_tax_account = self.env.ref(purchase_tax_ref, False)
        
        if not self.product_ids:
            product_ids = product_obj.search([('company_id', '=', company_id)])
        else:
            product_ids = self.product_ids
        vals = {}
        if self.customer_tax and sale_tax_account:
            vals.update({'taxes_id': [(6, 0, [sale_tax_account.id])]})
        if self.supplier_tax and purchase_tax_account:
            vals.update({'supplier_taxes_id': [(6, 0, [purchase_tax_account.id])]})
        product_ids.write(vals)
        return {'type': 'ir.actions.act_window_close'}
