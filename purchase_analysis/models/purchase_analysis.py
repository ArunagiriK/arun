# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError


class PurchaseAnalysis(models.Model):
    _name = "purchase.analysis"

    name = fields.Char(string="Analysis Name", readonly=1)
    analysis_period_from = fields.Date(string="Analysis Period From", required=True)
    analysis_period_to = fields.Date(string="Analysis Period To", required=True)
    projected_period_from = fields.Date(string="Projected Period From", required=True)
    projected_period_to = fields.Date(string="Projected Period To", required=True)
    by_vendor = fields.Boolean(String="By Vendor")
    vendor_ids = fields.Many2many('res.partner', string="Vendor")
    product_ids = fields.Many2many('product.product', string='Product')
    product_category_ids = fields.Many2many('product.category', string="Product Category")
    product_variant_attribute_ids = fields.Many2many('product.attribute', string="Product Variant Attribute")
    product_brand_ids = fields.Many2many('product.brand', string="Product Brand")
    analysis_lines_ids = fields.One2many('purchase.analysis.line', 'purchase_analysis_id', string="Analysis Lines")
    current_date = fields.Date.today()
    seller_all_lines = fields.Boolean(string="Seller All Lines")
    purchase_order_ids = fields.One2many('purchase.order', 'purchase_analysis_id', string='Purchase Orders')
    purchase_order_count = fields.Integer(string='PO', compute='_compute_count', store=True)

    @api.multi
    def compute_analysis_line(self):
        if self.analysis_period_from > self.analysis_period_to:
            raise UserError(" Analysis Period 'To Date' is lesser than 'From Date'.Please check the date")
        if self.analysis_period_from > self.current_date:
            raise UserError(" Analysis Period 'From Date' is greater than 'Current Date'.Please check the date")
        from_date = str(self.analysis_period_from) + ' ' + '00:00:00'
        to_date = str(self.analysis_period_to) + ' ' + '23:23:59'
        days = (self.analysis_period_to - self.analysis_period_from).days + 1
        self.analysis_lines_ids = False
        domain = [('order_id.confirmation_date', '>=', from_date), ('order_id.confirmation_date', '<=', to_date),
                  ('state', '=', 'sale')]
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.product_category_ids:
            domain.append(('product_id.categ_id', 'in', self.product_category_ids.ids))
        if self.product_variant_attribute_ids:
            domain.append(('product_id.attribute_line_ids.attribute_id', 'in', self.product_variant_attribute_ids.ids))
        if self.vendor_ids:
            domain.append(('product_id.seller_ids.name', 'in', self.vendor_ids.ids))
        if self.product_brand_ids:
            domain.append(('product_id.product_brand_id', 'in', self.product_brand_ids.ids))

        sale_order_line = self.env['sale.order.line'].search(domain)

        # compute current date + duration

        current_date = self.current_date.replace(self.current_date.year - 1)
        end_date = current_date + timedelta(days=days)
        from_date_projected = str(current_date) + ' ' + '00:00:00'
        to_date_projected = str(end_date) + ' ' + '23:23:59'
        domain_projected = [('order_id.confirmation_date', '>=', from_date_projected),
                            ('order_id.confirmation_date', '<=', to_date_projected),
                            ('state', '=', 'sale')]
        if self.product_ids:
            domain_projected.append(('product_id', 'in', self.product_ids.ids))
        if self.product_category_ids:
            domain_projected.append(('product_id.categ_id', 'in', self.product_category_ids.ids))
        if self.product_variant_attribute_ids:
            domain_projected.append(
                ('product_id.attribute_line_ids.attribute_id', 'in', self.product_variant_attribute_ids.ids))
        if self.vendor_ids:
            domain_projected.append(('product_id.seller_ids.name', 'in', self.vendor_ids.ids))
        if self.product_brand_ids:
            domain_projected.append(('product_id.product_brand_id', 'in', self.product_brand_ids.ids))
        sale_order_line_projected = self.env['sale.order.line'].search(domain_projected)

        # compute current date + projected date

        if self.current_date > self.projected_period_from:
            raise UserError("Projected Period 'From Date' is lesser than 'Current Date'.Please check the date")
        if self.projected_period_from > self.projected_period_to:
            raise UserError(" Projected Period 'To Date' is lesser than 'From Date'.Please check the date")
        current_date = self.current_date.replace(self.current_date.year - 1)
        projected_period_from = self.projected_period_from.replace(self.projected_period_from.year - 1)
        projected_from_date = str(current_date) + ' ' + '00:00:00'
        projected_to_date = str(projected_period_from) + ' ' + '23:23:59'
        projected_days = (self.projected_period_from - self.current_date).days + 1

        projected_domain = [('order_id.confirmation_date', '>=', projected_from_date),
                            ('order_id.confirmation_date', '<=', projected_to_date),
                            ('state', '=', 'sale')]
        if self.product_ids:
            projected_domain.append(('product_id', 'in', self.product_ids.ids))
        if self.product_category_ids:
            projected_domain.append(('product_id.categ_id', 'in', self.product_category_ids.ids))
        if self.product_variant_attribute_ids:
            projected_domain.append(
                ('product_id.attribute_line_ids.attribute_id', 'in', self.product_variant_attribute_ids.ids))
        if self.vendor_ids:
            projected_domain.append(('product_id.seller_ids.name', 'in', self.vendor_ids.ids))
        if self.product_brand_ids:
            projected_domain.append(('product_id.product_brand_id', 'in', self.product_brand_ids.ids))

        projected_sale_order_line = self.env['sale.order.line'].search(projected_domain)

        test_vendor = self.env['res.partner'].search([('test_vendor', '=', True)])

        products = []
        product_list = []
        for line in sale_order_line:
            if line.product_id not in products:
                products.append(line.product_id)
        for product in products:
            product_lines = sale_order_line.filtered(lambda l: l.product_id == product)
            product_unit_of_measure = ''
            if product_lines:
                product_unit_of_measure = product_lines[0].product_uom.id
            product_total_qty = sum(product_lines.mapped('product_uom_qty'))  # product qty :- analysis period
            average_sale = product_total_qty / days  # average sale :- analysis period
            vendors = product.variant_seller_ids
            lead_time = 0
            vendor_name = ''
            if vendors:
                lead_time = min(vendors.mapped('delay'))
                for vendor in vendors:
                    if vendor.delay == lead_time:
                        vendor_name = vendor.id
            else:
                if test_vendor:
                    vendor_name = test_vendor[0].id
                else:
                    vendor_name = ''

            product_lines_projected = sale_order_line_projected.filtered(lambda l: l.product_id == product)
            product_total_qty_projected = sum(
                product_lines_projected.mapped('product_uom_qty'))  # pdct qty :- current + days
            average_sale_projected = product_total_qty_projected / days  # avg sale :- current + days
            if product_lines_projected:
                days_in_stock_projected = product.qty_available / average_sale_projected
                # days in stock :- current + days
            else:
                days_in_stock_projected = 0
            projected_stock = round(average_sale_projected * projected_days)  # stock :- projected period
            stock_in_hand_projected_date = \
                product.qty_available - projected_stock  # stock in hand :- projected from  date
            procurement_qty = product_total_qty - stock_in_hand_projected_date
            projected_product_lines = projected_sale_order_line.filtered(lambda l: l.product_id == product)
            projected_product_total_qty = sum(
                projected_product_lines.mapped('product_uom_qty'))  # pdct qty :- projected period
            projected_average_sale = projected_product_total_qty / projected_days  # avg sale :- projected period
            if projected_product_lines:
                projected_stock_available_days = round(stock_in_hand_projected_date / projected_average_sale)
            else:
                projected_stock_available_days = 0
            projected_stock_available_date = self.projected_period_from + timedelta(days=projected_stock_available_days)
            next_procurement_date = projected_stock_available_date - timedelta(days=lead_time)
            variants = []
            values = []
            for variant in product.attribute_line_ids:
                variants.append(variant.display_name)
                for value in variant.value_ids:
                    values.append(value.name)
            product_dict = {'product_id': product.id, 'average_daily_sale_current': average_sale,
                            'stock_in_hand': product.qty_available, 'product_category': product.categ_id.display_name,
                            'product_description':
                                product.default_code + ' ' + product.name if product.default_code else product.name,
                            'days_in_stock': days_in_stock_projected,
                            'average_daily_sale_projected': average_sale_projected,
                            'Variant_attribute01': variants if len(variants) >= 1 else ' ',
                            'Variant_attribute_value': values if len(variants) >= 1 else '',
                            'stock_in_hand_projected_date': stock_in_hand_projected_date,
                            'procurement_qty': procurement_qty,
                            'delivery_lead_days': lead_time if vendors else '',
                            'next_procurement_date': next_procurement_date if procurement_qty > 0 else '',
                            'vendor': vendor_name, 'unit_price': product.lst_price,
                            'product_unit_of_measure': product_unit_of_measure,
                            'product_brand': product.product_brand_id.name if product.product_brand_id else ''}
            product_list.append((0, 0, product_dict))
        self.analysis_lines_ids = product_list

    @api.onchange('seller_all_lines')
    def _onchange_seller_all_lines(self):
        if self.seller_all_lines:
            for result in self.analysis_lines_ids:
                result.include_in_po = True
        else:
            for result in self.analysis_lines_ids:
                result.include_in_po = False

    @api.multi
    def create_po(self):
        vendors = []
        for result in self.analysis_lines_ids:
            if result.include_in_po and result.procurement_qty > 0:
                if result.vendor not in vendors:
                    vendors.append(result.vendor)
        for vendor in vendors:
            if vendor:
                product_list = []
                for order_line in self.analysis_lines_ids:
                    if order_line.include_in_po:
                        if vendor == order_line.vendor:
                            product_dict = {
                                'product_id': order_line.product_id.id,
                                'name': order_line.product_description,
                                'product_qty': order_line.procurement_qty,
                                'date_planned': self.current_date,
                                'price_unit': order_line.unit_price,
                                'product_uom': order_line.product_unit_of_measure,
                            }
                            product_list.append((0, 0, product_dict))
                purchase_dict = {
                    'partner_id': vendor,
                    'purchase_analysis_id': self.id,
                    'origin': self.name,
                    'order_line': product_list
                }
                purchase_order = self.env['purchase.order'].create(purchase_dict)
            else:
                for order_line in self.analysis_lines_ids:
                    if order_line.include_in_po:
                        if vendor == order_line.vendor:
                            raise UserError("'%s' should have associated vendor to create purchase order" % (
                                order_line.product_description))

    @api.multi
    def action_view_purchase_order(self):
        if self.purchase_order_ids:
            entries = self.purchase_order_ids
            return {
                'name': 'Purchase Order',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', entries.ids)]
            }

    @api.multi
    def action_pivot_view(self):
        if self.analysis_lines_ids:
            entries = self.analysis_lines_ids
            return {
                'name': 'Purchase Analysis',
                'view_type': 'form',
                'view_mode': 'pivot,tree,form',
                'res_model': 'purchase.analysis.line',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', entries.ids)]
            }

    @api.depends('purchase_order_ids', 'purchase_order_count')
    def _compute_count(self):
        for rec in self:
            if rec.purchase_order_ids:
                rec.purchase_order_count = len(rec.purchase_order_ids)
            else:
                rec.purchase_order_count = 0

    @api.model
    def create(self, vals):
        result = super(PurchaseAnalysis, self).create(vals)

        if result.product_category_ids:
            result.name = 'Purchase Analysis For' + "  " + str(result.projected_period_to) + " - " + \
                          str(result.projected_period_from)
            for rec in result.product_category_ids:
                result.name = result.name + " - " + rec.display_name + " "
        elif result.product_ids:
            result.name = 'Purchase Analysis For' + "  " + str(result.projected_period_to) + " - " + \
                          str(result.projected_period_from)
            for rec in result.product_ids:
                result.name = result.name + "-" + rec.name
        elif result.product_brand_ids:
            result.name = 'Purchase Analysis For' + "  " + str(result.projected_period_to) + " - " + \
                          str(result.projected_period_from)
            for rec in result.product_brand_ids:
                result.name = result.name + "-" + rec.name
        elif result.product_variant_attribute_ids:
            result.name = 'Purchase Analysis For' + "  " + str(result.projected_period_to) + " - " + \
                          str(result.projected_period_from)
            for rec in result.product_variant_attribute_ids:
                result.name = result.name + "-" + rec.name
        else:
            result.name = 'Purchase Analysis For' + "  " + str(result.projected_period_from) + " -- " + \
                          str(result.projected_period_to)

        return result


class PurchaseAnalysisLine(models.Model):
    _name = 'purchase.analysis.line'

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    purchase_analysis_id = fields.Many2one('purchase.analysis', readonly=True)
    product_description = fields.Char(string='Product Description', readonly=True)
    product_category = fields.Char(string='Product Category', readonly=True)
    Variant_attribute01 = fields.Char(string="Variant Attribute", readonly=True)
    Variant_attribute_value = fields.Char(string="Variant Attribute Value", readonly=True)
    stock_in_hand = fields.Float(string="SOH", readonly=True)
    average_daily_sale_current = fields.Float(string="Avg Daily Sale Current", readonly=True)
    average_daily_sale_projected = fields.Float(string="Avg Daily Sale Projected", readonly=True)
    days_in_stock = fields.Float(string="Days In Stock", readonly=True)
    delivery_lead_days = fields.Float(string="Delivery Lead Days", readonly=True)
    next_procurement_date = fields.Date(string="Next Procurement Date", readonly=True)
    procurement_qty = fields.Float(string="Procurement Qty", readonly=True)
    # projected_product_id = fields.Many2one('product.product', string='Product Projected')
    projected_total_sale_qty = fields.Float('Total Sale Qty', readonly=True)
    stock_in_hand_projected_date = fields.Float("SOH in Projected Date", readonly=True)
    include_in_po = fields.Boolean("Include In PO")
    vendor = fields.Char(readonly=True)
    unit_price = fields.Float(string="Unit Price", readonly=True)
    product_unit_of_measure = fields.Char(readonly=True)
    po_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                                 compute='_compute_po_status', String="PO Status")
    product_brand = fields.Char("Product Brand")

    @api.depends('include_in_po')
    def _compute_po_status(self):
        for result in self:
            if result.include_in_po:
                result.po_status = 'draft'


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_analysis_id = fields.Many2one('purchase.analysis')


class Respartner(models.Model):
    _inherit = "res.partner"

    test_vendor = fields.Boolean('Test Vendor')
