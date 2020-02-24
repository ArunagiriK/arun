from odoo import models, api, fields


#~ class ProductTemplate(models.Model):
    #~ _inherit = 'product.template'

    #~ article_no = fields.Char(string='Article Number')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # @api.depends('stock_quant_ids')
    # def _compute_average_land_cost(self):
    #     """
    #     this computing function will check all the stock quant related to this product. calculate average land cost
    #     :return:  average land cost
    #     """
    #     for product in self:
    #         if product.type == 'product' and product.stock_quant_ids:
    #             for quant in product.stock_quant_ids:
    #
    #
    #
    # average_land_cost = fields.Float(string='Average Land Cost', compute='_compute_average_land_cost')
    product_information_ids = fields.Many2many('product.information.line',string='Product Information')
    product_information_line_ids = fields.One2many('product.information.line', 'product_id',
                                                   string='Product Information')


class ProductInformationLine(models.Model):
    _name = 'product.information.line'
    
    product_info_id = fields.Many2one('product.information', required=True, string='Information Type')
    name = fields.Char('Value', required=True)
    product_id = fields.Many2one('product.product', ondelete='cascade')
    
    @api.multi
    def name_get(self):
        if not self._context.get('info_attribute', True):  # TDE FIXME: not used
            return super(ProductInformationLine, self).name_get()
        return [(value.id, "%s: %s" % (value.product_info_id.name, value.name)) for value in self]

    @api.multi
    def _info_name(self, info_attributes):
        return ", ".join([v.name for v in self if v.product_info_id in info_attributes])
