# -*- coding: utf-8 -*-
import logging
import time
from datetime import date
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang, format_date
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
from lxml import etree
_logger = logging.getLogger(__name__)

class AccountMoveTemplate(models.Model):
    _name = "account.move.template"
    _description = "Journal Entries"
    #~ _order = 'date desc, id desc'
    
    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id 
    
    @api.multi
    def create_account_move_one(self):
        if self.from_journal_id:
            line_ids = []
            for line in self.from_line_ids:
                print('line.company_currency_id.id : ', line.company_currency_id.id)
                line_ids.append((0,0,{'tax_line_id': line.tax_line_id.id,
                                      'account_id': line.account_id.id,
                                      'partner_id': line.partner_id.id,
                                      'name': line.name,
                                      'analytic_account_id': line.analytic_account_id.id,
                                      'analytic_tag_ids': line.analytic_tag_ids,
                                      'amount_currency': line.amount_currency,
                                      'company_currency_id': line.company_currency_id.id,
                                      'company_id': line.company_id.id,
                                      'currency_id': line.currency_id.id,
                                      'debit': line.debit,
                                      'credit': line.credit,
                                      'tax_ids': line.tax_ids.ids,
#                                       'tax_ids': [(6, 0, line.tax_ids)],
                                      'date_maturity': line.date_maturity,
                                      'recompute_tax_line': line.recompute_tax_line,
                                      'tax_line_grouping_key': line.tax_line_grouping_key}))
                
            account_move_obj = self.env['account.move'].create({'date': self.from_date,
                                                                 'ref': self.from_ref,
                                                                 'journal_id': self.from_journal_id.id,
                                                                 'company_id': self.from_company_id.id,
                                                                 'currency_id': self.from_currency_id.id,
                                                                 'line_ids': line_ids,
                                                                 'narration': self.from_narration})
            if account_move_obj:
                self.hide_from_creation_button = True
            print('--------------------------------------------------------------')
            print('account_move_obj  : ', account_move_obj)
            print('--------------------------------------------------------------')
            
    @api.multi
    def create_account_move_two(self):
        if self.to_journal_id:
            line_ids = []
            for line in self.to_line_ids:
                print('line.company_currency_id.id : ', line.company_currency_id.id)
                line_ids.append((0,0,{'tax_line_id': line.tax_line_id.id,
                                      'account_id': line.account_id.id,
                                      'partner_id': line.partner_id.id,
                                      'name': line.name,
                                      'analytic_account_id': line.analytic_account_id.id,
                                      'analytic_tag_ids': line.analytic_tag_ids,
                                      'amount_currency': line.amount_currency,
                                      'company_currency_id': line.company_currency_id.id,
                                      'company_id': line.company_id.id,
                                      'currency_id': line.currency_id.id,
                                      'debit': line.debit,
                                      'credit': line.credit,
                                      'tax_ids': line.tax_ids.ids,
#                                       'tax_ids': [(6, 0, line.tax_ids)],
                                      'date_maturity': line.date_maturity,
                                      'recompute_tax_line': line.recompute_tax_line,
                                      'tax_line_grouping_key': line.tax_line_grouping_key}))
                
            account_move_obj = self.env['account.move'].create({'date': self.to_date,
                                                                 'ref': self.to_ref,
                                                                 'journal_id': self.to_journal_id.id,
                                                                 'company_id': self.to_company_id.id,
                                                                 'currency_id': self.to_currency_id.id,
                                                                 'line_ids': line_ids,
                                                                 'narration': self.to_narration})
            if account_move_obj:
                self.hide_to_creation_button = True
            print('--------------------------------------------------------------')
            print('account_move_obj  : ', account_move_obj)
            print('--------------------------------------------------------------')
            
    
    from_name = fields.Char(string='Number', required=True, copy=False, default='/')
    from_date = fields.Date(required=True, index=True, default=fields.Date.context_today)
    from_ref = fields.Char(string='Reference', copy=False)
    from_journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    from_company_id = fields.Many2one('res.company',related='from_journal_id.company_id'  ,string='Company')
    from_amount = fields.Float('Amount')
    from_currency_id = fields.Many2one('res.currency',  store=True, string="Currency")
    from_line_ids = fields.One2many('account.move.line.child.one', 'move_id', string='Journal Items')
    from_matched_percentage = fields.Float('Percentage Matched', digits=0, store=True, readonly=True, help="Technical field used in cash basis method")
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status',
      required=True, readonly=True, copy=False, default='draft',
      help='All manually created new journal entries are usually in the status \'Unposted\', '
           'but you can set the option to skip that status on the related journal. '
           'In that case, they will behave as journal entries automatically created by the '
           'system on document validation (invoices, bank statements...) and will be created '
           'in \'Posted\' status.')
    from_partner_id = fields.Many2one('res.partner',  string="Partner", store=True, readonly=True)
    from_narration = fields.Text(string='Internal Note')
    hide_from_creation_button = fields.Boolean('Hide From Creation')
    # TO
    to_name = fields.Char(string='Number', required=True, copy=False, default='/')
    to_date = fields.Date(required=True, states={'posted': [('readonly', True)]}, index=True, default=fields.Date.context_today)
    to_ref = fields.Char(string='Reference', copy=False)
    to_journal_id = fields.Many2one('account.journal', string='Journal', required=True, states={'posted': [('readonly', True)]})
    to_company_id = fields.Many2one('res.company', related='to_journal_id.company_id', string='Company')
    to_amount = fields.Float('Amount')
    to_currency_id = fields.Many2one('res.currency' ,store=True, string="Currency")
    to_line_ids = fields.One2many('account.move.line.child.two', 'move_id', string='Journal Items')
    to_matched_percentage = fields.Float('Percentage Matched', digits=0, store=True, readonly=True, help="Technical field used in cash basis method")
    to_partner_id = fields.Many2one('res.partner',  string="Partner", store=True, readonly=True)
    to_narration = fields.Text(string='Internal Note')
    hide_to_creation_button = fields.Boolean('To From Creation')

    @api.multi
    def action_duplicate(self):
        self.ensure_one()
        action = self.env.ref('account_journal_child.action_inherited_move_template_line').read()[0]
        action['context'] = dict(self.env.context)
        action['context']['form_view_initial_mode'] = 'edit'
        action['context']['view_no_maturity'] = False
        action['views'] = [(self.env.ref('account.view_inherited_move_template_form').id, 'form')]
        action['res_id'] = self.copy().id
        return action
    

    
class AccountMoveLineChildOne(models.Model):
    _name = "account.move.line.child.one"
    _description = "Journal Item"
    
    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id 
        
    move_id = fields.Many2one('account.move.template', string='Journal Entry', ondelete="cascade")
    
    account_id = fields.Many2one('account.account', string='Account', required=True,
        ondelete="cascade", domain=[('deprecated', '=', False)], default=lambda self: self._context.get('account_id', False))
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    name = fields.Char(string="Label")
    debit = fields.Float(default=0.0)
    credit = fields.Float(default=0.0)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    tax_ids = fields.Many2many('account.tax', string='Taxes Applied', domain=['|', ('active', '=', False), ('active', '=', True)], help="Taxes that apply on the base amount")
    company_id = fields.Many2one('res.company',related='account_id.company_id', string='Company')
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id', string="Currency")
    amount_currency = fields.Monetary(default=0.0, help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    date_maturity = fields.Date(string='Due date', index=True, required=True,
        help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")
    recompute_tax_line = fields.Boolean(store=False, help="Technical field used to know if the tax_ids field has been modified in the UI.")
    tax_line_grouping_key = fields.Char(store=False, string='Old Taxes', help="Technical field used to store the old values of fields used to compute tax lines (in account.move form view) between the moment the user changed it and the moment the ORM reflects that change in its one2many")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True,
        help='Utility field to express amount currency', store=True)
#     narration = fields.Text(string='Narration', readonly=False)
#     ref = fields.Char(string='Reference', store=True, copy=False, index=True, readonly=False)
#     payment_id = fields.Many2one('account.payment', string="Originator Payment", help="Payment that created this entry", copy=False)
#     journal_id = fields.Many2one('account.journal', string='Journal', readonly=False,
#         index=True, store=True, copy=False)  # related is required
#     date = fields.Date(string='Date', index=True, store=True, copy=False, readonly=False)  # related is required
#     
    tax_line_id = fields.Many2one('account.tax', string='Originator tax', ondelete='restrict',
        help="Indicates that this journal item is a tax line")
#     analytic_line_ids = fields.One2many('account.analytic.line', 'move_id', string='Analytic lines', oldname="analytic_lines")
    
class AccountMoveLineChildTwo(models.Model):
    _name = "account.move.line.child.two"
    _description = "Journal Item"
    
    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id 
        
    move_id = fields.Many2one('account.move.template', string='Journal Entry', ondelete="cascade")
    
    account_id = fields.Many2one('account.account', string='Account', required=True,
        ondelete="cascade", domain=[('deprecated', '=', False)], default=lambda self: self._context.get('account_id', False))
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    name = fields.Char(string="Label")
    debit = fields.Float(default=0.0)
    credit = fields.Float(default=0.0)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    tax_ids = fields.Many2many('account.tax', string='Taxes Applied', domain=['|', ('active', '=', False), ('active', '=', True)], help="Taxes that apply on the base amount")
    company_id = fields.Many2one('res.company',related='account_id.company_id', string='Company')
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id', string="Currency")
    amount_currency = fields.Monetary(default=0.0, help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    date_maturity = fields.Date(string='Due date', index=True, required=True,
        help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")
    recompute_tax_line = fields.Boolean(store=False, help="Technical field used to know if the tax_ids field has been modified in the UI.")
    tax_line_grouping_key = fields.Char(store=False, string='Old Taxes', help="Technical field used to store the old values of fields used to compute tax lines (in account.move form view) between the moment the user changed it and the moment the ORM reflects that change in its one2many")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True,
        help='Utility field to express amount currency', store=True)
#     narration = fields.Text(string='Narration', readonly=False)
#     ref = fields.Char(string='Reference', store=True, copy=False, index=True, readonly=False)
#     payment_id = fields.Many2one('account.payment', string="Originator Payment", help="Payment that created this entry", copy=False)
#     journal_id = fields.Many2one('account.journal', string='Journal', readonly=False,
#         index=True, store=True, copy=False)  # related is required
#     date = fields.Date(string='Date', index=True, store=True, copy=False, readonly=False)  # related is required
#     
    tax_line_id = fields.Many2one('account.tax', string='Originator tax', ondelete='restrict',
        help="Indicates that this journal item is a tax line")
#     analytic_line_ids = fields.One2many('account.analytic.line', 'move_id', string='Analytic lines', oldname="analytic_lines")
    
    
