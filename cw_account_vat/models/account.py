# -*- coding: utf-8 -*-

from ast import literal_eval
from operator import itemgetter
import time

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError
# from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP


TAX_TYPE_SELECTION = [
    ('vat', 'Vat Registered'),
    ('non_vat', 'Non Vat Registered'),
    ('gcc_vat', 'GCC Vat Registered'),
    ('non_gcc_vat', 'GCC Non Vat Registered'),
    ('non_gcc', 'Non GCC'),
    ('vat_des', 'Vat Registered - Designated Zone'),
    ('non_vat_des', 'Non Vat Registered - Designated Zone'),
]

class Partner(models.Model):
    _inherit = "res.partner"
    
    tax_type = fields.Selection(TAX_TYPE_SELECTION, required=True, default='vat', string="Tax Type")
    place_supply_state_id = fields.Many2one("res.country.state", string='Place of Supply State', ondelete='restrict')
    place_supply_country_id = fields.Many2one('res.country', string='Place of Supply Country', ondelete='restrict')
    place_supply_country_code = fields.Char(related='place_supply_country_id.code', readonly=True)
    

    @api.onchange('place_supply_state_id')
    def _onchange_place_supply_state_id(self):
        if self.place_supply_state_id:
            self.place_supply_country_id = self.place_supply_state_id.country_id and self.place_supply_state_id.country_id.id or False
            self.place_supply_country_code = self.place_supply_state_id.country_id and self.place_supply_state_id.country_id.code or False            
    

    @api.onchange('place_supply_country_id')
    def _onchange_place_supply_country_id(self):
        res = {'domain': {'place_supply_state_id': []}}
        if self.place_supply_country_id:
            res = {'domain': {'place_supply_state_id': [('country_id', '=', self.place_supply_country_id.id)]}}
            self.place_supply_country_code = self.place_supply_country_id.code
            if self.place_supply_state_id and self.place_supply_state_id.country_id != self.place_supply_country_id:
                self.place_supply_state_id = False            
        return res
    
    
    @api.onchange('tax_type')
    def _onchange_tax_type(self):
        res = {}
        if self.tax_type:
            fp_domain = [('tax_type', '=', self.tax_type)]
            if self.company_id:
                fp_domain.extend(['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)])
            self.property_account_position_id = self.env['account.fiscal.position'].search(fp_domain, limit=1)
        return res
    

class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'
    
    tax_type = fields.Selection(TAX_TYPE_SELECTION, string="Tax Type")
    
    
class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'
    
    tax_type = fields.Selection(TAX_TYPE_SELECTION, string="Tax Type")
        

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    tax_type = fields.Selection(TAX_TYPE_SELECTION, related='fiscal_position_id.tax_type', string='Tax Type', readonly=True, store=True)
    
    def _prepare_tax_line_vals(self, line, tax): 
        #self = self.with_context(inv_type=self.type)       
        #https://tallysolutions.com/mena/place-of-supply/place-supply-export-goods/
        #https://books.zoho.com/app#/contacts/1406017000000065248/edit
        res = super(AccountInvoice, self)._prepare_tax_line_vals(line, tax)
        return res


class AccountInvoiceline(models.Model):
    _inherit = 'account.invoice.line'    
    
    
class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"
    

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
            
    partner_state_id = fields.Many2one('res.country.state', related='partner_id.state_id', string='State', readonly=True, store=True)
    partner_country_id = fields.Many2one('res.country', related='partner_id.country_id', string='Country', readonly=True, store=True)
    partner_place_supply_state_id = fields.Many2one('res.country.state', related='partner_id.place_supply_state_id', string='Place Supply of State', readonly=True, store=True)
    partner_place_supply_country_id = fields.Many2one('res.country', related='partner_id.place_supply_country_id', string='Place Supply of Country', readonly=True, store=True)
    invl_id = fields.Many2one('account.invoice.line')
    invoice_tax_line_id = fields.Many2one('account.invoice.tax')


class ProductProduct(models.Model):
    _inherit = "product.product"
    
    @api.model
    def _convert_prepared_anglosaxon_line(self, line, partner):
        res = super(ProductProduct, self)._convert_prepared_anglosaxon_line(line, partner)
        res.update({'invl_id': line.get('invl_id', False),
                    'invoice_tax_line_id': line.get('invoice_tax_line_id', False),})
        return res
    

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'
            
    type = fields.Selection([('regular', 'Regular'), ('zero', 'Zero'), ('exempt', 'Exempt'), ('out_scope', 'Out of Scope'), ('reverse', 'Reverse')], required=True, default='regular', string="Type")


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        tax_type = context.get('tax_type', False)
        type = context.get('type', False)
        if tax_type and tax_type in ['gcc_vat', 'non_gcc_vat', 'non_gcc', 'vat_des', 'non_vat_des']:
            type = False     
        return super(AccountTax, self.with_context(type=type)).search(args, offset, limit, order, count=count)
    
    