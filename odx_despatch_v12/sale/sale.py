# -*- coding: utf-8 -*-
from odoo import models,api,fields
import itertools
import odoo.addons.decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = "sale.order"
#     order_line2 = fields.One2many('sale.order.line','order_id',string="Packaging Order Line")
    
#     def od_get_amount_all(self):
#         """
#         Compute the total amounts of the SO.
#         """
#         res = {}
#         for order in self:
#             amount_untaxed = amount_tax = 0.0
#             for line in order.order_line:
#                 amount_untaxed += line.price_subtotal
#                 amount_tax += line.price_tax
#             res.update({
#                 'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
#                 'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
#                 'amount_total': amount_untaxed + amount_tax,
#             })
#         return res
#     def button_dummy(self):
#         res = self.od_get_amount_all()
#         self.write(res)
#     @api.model
#     def create(self,vals):
#         res = self.od_get_amount_all()
#         vals.update(res)
#         return super(SaleOrder,self).create(vals)
#     @api.multi
#     def write(self,vals):
#         res = self.od_get_amount_all()
#         vals.update(res)
#         return super(SaleOrder,self).write(vals)




    @api.model
    def create(self, vals):

        result = super(SaleOrder, self).create(vals)
        pricelist_id = result.pricelist_id
        od_discount = pricelist_id.od_discount
        result.od_discount = od_discount
        return result


    
    @api.onchange('pricelist_id')
    def onchange_od_pricelist_id(self):
        discount = self.pricelist_id and self.pricelist_id.od_discount
        self.od_discount = discount
    
    od_carton_no = fields.Char(string="Carton")
    od_packaging_no = fields.Char(string="Packaging")
    od_discount = fields.Float(string="Discount")
    od_category_id = fields.Many2one('orchid.category',string="Category")
    od_type_id = fields.Many2one('orchid.partner.type', string='Type')
    od_area_id = fields.Many2one('orchid.partner.area', string='Area')
    od_deliveryloc_id = fields.Many2one('od.delivery.loc',string='Delivery Location')
    od_group_id = fields.Many2one('orchid.partner.group',string='Group')
#     amount_untaxed = fields.Monetary(string='Untaxed Amount', readonly=True,  track_visibility='always')
#     amount_tax = fields.Monetary(string='Taxes',readonly=True, track_visibility='always')
#     amount_total = fields.Monetary(string='Total',readonly=True,track_visibility='always')
    local_currency = fields.Float(string='Local Currency', store=True, readonly=True, compute='_amount_all', track_visibility='always', digits=dp.get_precision('Global'))

    _sql_constraints = [
    ('partner_client_code_uniq', 'unique (partner_id,client_order_ref)', 'Reference  should be unique for Partner!')
    ]
    
    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            company = self.env['res.company'].browse(self.env.user.company_id.id)
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'local_currency': order.pricelist_id.currency_id.compute((amount_untaxed + amount_tax),company.currency_id)
            })

    
    @api.multi 
    def od_update_discount(self):
        discount =   self.od_discount or 0.0
        for line in self.order_line:
            if discount:
                line['discount'] = discount
    
    @api.multi 
    def od_update_article(self):
        pricelist_id =   self.pricelist_id and self.pricelist_id.id or False
        for line in self.order_line:
            product_id = line.product_id and line.product_id.id or False
            if product_id and pricelist_id:
                pricelist_item = self.env['product.pricelist.item']
                pricelist_ob = pricelist_item.search([('product_id','=',product_id),('pricelist_id','=',pricelist_id)],limit=1)
                if pricelist_ob:
                    od_article_no = pricelist_ob.od_article_no
                    line['od_article_no'] = od_article_no
    
    
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        invoice_vals = super(SaleOrder,self)._prepare_invoice()
        od_carton_no = self.od_carton_no
        od_deliveryloc_id = self.od_deliveryloc_id and self.od_deliveryloc_id.id
        od_requested_date = self.requested_date or False
        od_type_id = self.od_type_id and self.od_type_id.id or False
        od_category_id = self.od_category_id and self.od_category_id.id or False
        od_area_id = self.od_area_id and self.od_area_id.id or False
        od_group_id = self.od_group_id and self.od_group_id.id or False
        od_packaging_no = self.od_packaging_no
        invoice_vals.update({
            'od_carton_no':od_carton_no,
            'od_packaging_no':od_packaging_no,
            'od_deliveryloc_id':od_deliveryloc_id,
            'od_requested_date':od_requested_date,
            'od_type_id':od_type_id,
            'od_category_id':od_category_id,
            'od_area_id':od_area_id,
            'od_group_id':od_group_id
                             })
        return invoice_vals
        
    @api.model
    def _prepare_procurement_group(self):
        res = super(SaleOrder,self)._prepare_procurement_group()
        od_deliveryloc_id = self.od_deliveryloc_id and self.od_deliveryloc_id.id
        od_requested_date = self.requested_date or False
        res.update({'od_carton_no':self.od_carton_no,
                    'od_deliveryloc_id':od_deliveryloc_id,
                    'od_packaging_no':self.od_packaging_no,
                    'od_client_order_ref':self.client_order_ref,
                    'od_requested_date':od_requested_date,
                    'od_incoterm':self.incoterm and self.incoterm.id,
                    })
        return res

class SaleLine(models.Model):
    _inherit = "sale.order.line"
    od_item_code = fields.Char('Item Code')
    od_article_no = fields.Char('Article#')
    od_carton_no = fields.Char(string="Carton")
    od_packaging_no = fields.Char(string="Packaging")
    
    
    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        res = super(SaleLine,self)._prepare_order_line_procurement(group_id)
        res.update({'od_carton_no':self.od_carton_no,'od_packaging_no':self.od_packaging_no})
        return res
    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.
        :param qty: float quantity to invoice
        """
        res = super(SaleLine,self)._prepare_invoice_line(qty)
        res.update({'od_item_code':self.od_item_code,
                    'od_article_no':self.od_article_no,
                    'od_carton_no':self.od_carton_no,
                    'od_packaging_no':self.od_packaging_no,
                    })
        return res
#     @api.multi
#     @api.onchange('product_id')
#     def product_id_change(self):
#         res = super(SaleLine,self).product_id_change()
#         vals = {}
#         product = self.product_id.with_context(
#             lang=self.order_id.partner_id.lang,
#             partner=self.order_id.partner_id.id,
#             quantity=self.product_uom_qty,
#             date=self.order_id.date_order,
#             pricelist=self.order_id.pricelist_id.id,
#             uom=self.product_uom.id
#             )
#         product_id = product.id
#         pricelist_id =  self.order_id and self.order_id.pricelist_id and self.order_id.pricelist_id.id or False
#          
#         if product_id and pricelist_id:
#             
#             pricelist_item = self.env['product.pricelist.item']
#              
#             pricelist_ob = pricelist_item.search([('product_id','=',product_id),('pricelist_id','=',pricelist_id)],limit=1)
#              
#             if pricelist_ob:
#                 discount = pricelist_ob.price_discount or 0.0
#                 od_article_no = pricelist_ob.od_article_no
#                 od_item_code = pricelist_ob.od_item_code
#                 name = pricelist_ob.od_description
#                 vals.update({'discount':discount,'od_article_no':od_article_no,'od_item_code':od_item_code,'name':name})
#                 self.update(vals)
#         return res
#     
#     @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
#     def _onchange_discount(self):
# #         self.discount = 0.0
#         if not (self.product_id and self.product_uom and
#                 self.order_id.partner_id and self.order_id.pricelist_id and
#                 self.order_id.pricelist_id.discount_policy == 'without_discount' and
#                 self.env.user.has_group('sale.group_discount_per_so_line')):
#             return
#         context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id)
#         pricelist_context = dict(context_partner, uom=self.product_uom.id, date=self.order_id.date_order)
#  
#         price, rule_id = self.order_id.pricelist_id.with_context(pricelist_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
#         print "price rule>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",price,rule_id
#         new_list_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
#         print "new list price>>>>>>>>>>>>>>>>>>>,currency_id",new_list_price,currency_id
#         new_list_price = self.env['account.tax']._fix_tax_included_price(new_list_price, self.product_id.taxes_id, self.tax_id)
#  
#         if price != 0 and new_list_price != 0:
#             if self.product_id.company_id and self.order_id.pricelist_id.currency_id != self.product_id.company_id.currency_id:
#                 # new_list_price is in company's currency while price in pricelist currency
#                 ctx = dict(context_partner, date=self.order_id.date_order)
#                 new_list_price = self.env['res.currency'].browse(currency_id).with_context(ctx).compute(new_list_price, self.order_id.pricelist_id.currency_id)
#             discount = (new_list_price - price) / new_list_price * 100
#             if discount > 0:
#                 self.discount = discount
