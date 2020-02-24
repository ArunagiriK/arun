from odoo import api, exceptions, fields, models, _
from datetime import datetime
from dateutil import parser, relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class ProductSubstitutionWiz(models.TransientModel):
    _name = "product.substitution.wiz"

    product_master_id= fields.Many2one('product.product', string='Master Product')
    substitute_product_ids = fields.Many2many(comodel_name='product.product', relation='substitute_product_wiz_rel',
                                              column1='product_id', column2='substitute_id',
                                              string='Substitute Products')
    substitute_product_id = fields.Many2one('product.product', string='Substitute Product',required=True)

    @api.onchange('substitute_product_ids','product_master_id')
    def on_change_substitution_products(self):
        if self.substitute_product_ids:
            return {'domain': {'substitute_product_id': [('id', 'in', self.substitute_product_ids.ids)]}}
        else:
            return {'domain': {'substitute_product_id': [('id', 'in', [])]}}

    @api.multi
    def confirm_product(self):
        if self._context.get('active_id'):
            sale_order_line = self.env['sale.order.line'].browse(self._context.get('active_id'))
            if sale_order_line:
                if self.substitute_product_id:
                    sale_order_line.update({'product_id':self.substitute_product_id.id})
                    return sale_order_line.product_id_change()

    @api.model
    def default_get(self, default_fields):
        res = super(ProductSubstitutionWiz, self).default_get(default_fields)
        if self._context.get('active_id'):
            sale_order_line = self.env['sale.order.line'].browse(self._context.get('active_id'))
            if sale_order_line:
                product = sale_order_line.product_id
                substitution_products = product.substitute_product_ids
                res.update({'substitute_product_ids': [(6,0,substitution_products.ids)],
                            'product_master_id':product.id })
        return res