# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from pprint import pprint
from datetime import date
from odoo.osv import expression

class Picking(models.Model):
    _inherit = 'stock.picking'

    od_invoice_control = fields.Selection([('no_invoice','Not Applicable'),('to_invoice','To Be Invoiced'),('invoice_created','Invoice Already Created')],string="Invoice Control")
    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    
    def get_product_account(self,product):
        return (product.property_account_income_id and product.property_account_income_id.id) or (product.categ_id and product.categ_id.property_account_income_categ_id and  product.categ_id.property_account_income_categ_id.id) 

    
    def get_value_from_param(self,param):
        parameter_obj = self.env['ir.config_parameter']
        key =[('key', '=', param)]
        param_obj = parameter_obj.search(key)
        if not param_obj:
            raise Warning('NoParameter Not defined\nconfig it in System Parameters with %s'%param)
        result = param_obj.value
        return result
    
    
    def od_prepare_invoice_line_vals(self):
        res = []
        pricelist_id = self.partner_id.property_product_pricelist.id
        for line in self.move_ids_without_package:
            product = line.product_id.with_context(
                    lang = self.partner_id.lang,
                    partner = self.partner_id.id,
                    pricelist = self.partner_id.property_product_pricelist.id,
                    )
            credit_account_id = self.get_product_account(product)
            name = product.description_picking or product.name
            price_unit = product.lst_price
            uom_id = product.uom_id.id
            #~ pricelist_item = self.env['product.pricelist.item']
            #~ pricelist_ob = pricelist_item.search([('product_id','=',product.id),('pricelist_id','=',pricelist_id)],limit=1)
            #~ discount = pricelist_ob.price_discount or 0.0
            #~ pricelist_discount = 0
            #~ if self.partner_id.property_product_pricelist:
                #~ pricelist_discount = self.partner_id.property_product_pricelist.od_discount
            vals = {
                    'product_id': product.id,
                    'name': name,
                    'account_id': credit_account_id,
                    'price_unit': price_unit,
                    'quantity': line.quantity_done,
                    'uom_id': uom_id,
                    'invoice_line_tax_ids': [(6, 0, product.taxes_id.ids)] or [(6, 0, credit_account_id.tax_ids.ids)],
                    }
            res.append((0,0,vals))
        return res


    def od_prepare_invoice_vals(self):
        journal_id = int(self.get_value_from_param('customer_refund_journal_id'))
        partner = self.partner_id
        partner_id = partner.id
        user_id = partner.user_id and partner.user_id.id 
        if type(user_id) == 'tuple':
            user_id = user_id(0)
        if not user_id:
            user_id = self._uid
        pricelist_id = partner.property_product_pricelist and partner.property_product_pricelist.id
        currency_id = partner.property_product_pricelist and partner.property_product_pricelist.currency_id and partner.property_product_pricelist.currency_id.id or False
        account_id = partner.property_account_receivable_id and partner.property_account_receivable_id.id or False,
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')[:10]
        name = self.name
        vals = {'name':name,'journal_id':journal_id,
                'partner_id':partner_id,'account_id':account_id,
                'date':date,'type':'out_refund',
                'user_id':user_id,
                'od_pricelist_id':pricelist_id,
                'currency_id':currency_id}
        return vals

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_out_refund').read()[0]
        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        action['res_id'] = self.invoice_id.id
        return action

    @api.multi
    def od_button_create_invoice(self):
        self.ensure_one()
        #~ grv_picking_type_id =self.get_value_from_param('grv_picking_type_id')
        origin = self.origin
        picking_type_id = self.picking_type_id and self.picking_type_id.id or False
        #~ if str(picking_type_id) not in grv_picking_type_id:
            #~ raise Warning("Only GRV Support Invoice From Picking")
        invoice_pool = self.env['account.invoice']
        invoice_vals = self.od_prepare_invoice_vals()
        if invoice_vals:
        	if origin:
        		invoice_vals['name'] = invoice_vals['name'] + "(" +origin+")"
        invoice_vals['invoice_line_ids'] = self.od_prepare_invoice_line_vals()
        invoice = invoice_pool.create(invoice_vals)
        self.write({'invoice_id': invoice.id})
        
        #~ model_data = self.env['ir.model.data']
        tree_view = self.env.ref('account.action_invoice_tree1')
        form_view = self.env.ref('account.invoice_form')
        #~ tree_view = self.env.ref('account', 'invoice_tree')
        #~ form_view = self.env.ref('account', 'invoice_form')
        
        self.od_invoice_control = 'invoice_created'
        #~ value = {
                #~ 'name': _('Invoices'),
                #~ 'view_type': 'form',
                #~ 'view_mode': 'tree,form',
                #~ 'res_model': 'account.invoice',
                #~ 'domain' : [('id','=',invoice.id)],
                #~ 'views': [ (tree_view and tree_view or False, 'tree'),(form_view and form_view or False, 'form')],
                #~ 'type': 'ir.actions.act_window',
            
        #~ }
        #~ return value
    


