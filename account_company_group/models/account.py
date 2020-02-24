# -*- coding: utf-8 -*-

import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree



class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account"
    _order = "code"

    @api.multi
    @api.constrains('internal_type', 'reconcile')
    def _check_reconcile(self):
        for account in self:
            if account.internal_type in ('receivable', 'payable') and account.reconcile == False:
                raise ValidationError(_('You cannot have a receivable/payable account that is not reconcilable. (account code: %s)') % account.code)

    @api.multi
    @api.constrains('user_type_id')
    def _check_user_type_id(self):
        data_unaffected_earnings = self.env.ref('account.data_unaffected_earnings')
        result = self.read_group([('user_type_id', '=', data_unaffected_earnings.id)], ['company_id'], ['company_id'])
        for res in result:
            if res.get('company_id_count', 0) >= 2:
                account_unaffected_earnings = self.search([('company_id', '=', res['company_id'][0]), 
                                                           ('user_type_id', '=', data_unaffected_earnings.id)])
                raise ValidationError(_('You cannot have more than one account with "Current Year Earnings" as type. (accounts: %s)') % [a.code for a in account_unaffected_earnings])

    name = fields.Char(required=True, index=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency',
        help="Forces all moves for this account to have this account currency.")
    code = fields.Char(size=64, required=True, index=True)
    deprecated = fields.Boolean(index=True, default=False)
    user_type_id = fields.Many2one('account.account.type', string='Type', required=True, oldname="user_type",
        help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries.")
    internal_type = fields.Selection(related='user_type_id.type', string="Internal Type", store=True, readonly=True)
    internal_group = fields.Selection(related='user_type_id.internal_group', string="Internal Group", store=True, readonly=True)
    #has_unreconciled_entries = fields.Boolean(compute='_compute_has_unreconciled_entries',
    #    help="The account has at least one unreconciled debit and credit since last time the invoices & payments matching was performed.")
    last_time_entries_checked = fields.Datetime(string='Latest Invoices & Payments Matching Date', readonly=True, copy=False,
        help='Last time the invoices & payments matching was performed on this account. It is set either if there\'s not at least '\
        'an unreconciled debit and an unreconciled credit Or if you click the "Done" button.')
    reconcile = fields.Boolean(string='Allow Reconciliation', default=False,
        help="Check this box if this account allows invoices & payments matching of journal items.")
    tax_ids = fields.Many2many('account.tax', 'account_account_tax_default_rel',
        'account_id', 'tax_id', string='Default Taxes')
    note = fields.Text('Internal Notes')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    company_ids = fields.Many2many('res.company', string='Child Companies')
    tag_ids = fields.Many2many('account.account.tag', 'account_account_account_tag', string='Tags', help="Optional tags you may want to assign for custom reporting")
    group_id = fields.Many2one('account.group')
    opening_debit = fields.Monetary(string="Opening debit", compute='_compute_opening_debit_credit', inverse='_set_opening_debit', help="Opening debit value for this account.")
    opening_credit = fields.Monetary(string="Opening credit", compute='_compute_opening_debit_credit', inverse='_set_opening_credit', help="Opening credit value for this account.")

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the account must be unique per company !')
    ]
    
    #~ @api.onchange('company_id')
    #~ def _onchange_company_id(self):
        #~ self.company_ids = []
        #~ if self.company_id:
            #~ return {'domain': {'company_ids': [('parent_id', '=', self.company_id.id)]}}

    @api.multi
    def account_chart(self):
        self._cr.execute("select company_id from account_account where code=%s ", (self.code,))
        res = self.env.cr.dictfetchall()
        print(res)
        acc=[]
        account_obj = True
        for account in res:
            acc.append(account['company_id'])
        for company in self.company_ids:
            if company.id not in acc:
                account_obj = False
                print(company.name)
                print(company.id)
                chartof_account_for_child = self.create({'code':self.code,
                                                'name':self.name,
                                                'user_type_id':self.user_type_id.id,
                                                'company_id':company.id,
                                                'group_id':self.group_id.id,
                                                'reconcile':self.reconcile,
                                                'deprecated':self.deprecated,
                             })
        if account_obj:
           raise ValidationError(_('Ledger already exist'))
    
    
   
   
    @api.multi
    def delete_chart(self):
        for company in self.company_ids:
            if company.parent_id.id:
               self._cr.execute("select id from account_account where code=%s and company_id=%s", (self.code,company.id,))
               res = self.env.cr.dictfetchall()
               for account in res:
                   acc=account['id']
                   self.browse(acc).unlink()


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        company_ids = []
        for company_obj in self.env['res.company'].search([]):
            if company_obj.parent_id.id:
                company_ids.append(company_obj.id)
        child_company = self.env.context.get('child_company', False)
        parent_company = self.env.context.get('parent_company', False)
        if child_company == 'yes':
            args += [('company_id', 'in', company_ids)]
            #~ print('Child:',args)
        elif parent_company == 'yes':
            args += [('company_id', 'not in', company_ids)]
        return super(AccountAccount, self).search(args, offset, limit, order, count=count)

    
   #~ def fields_view_get(self, cr, uid, view_id=None, view_type='tree',context=None, toolbar=False, submenu=False):
        #~ if context is None:
           #~ context = {}
        #~ res = super(class_name, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        #~ group_id = self.pool.get('res.users').has_group(cr, uid, 'modulename.group_xml_id')
        #~ doc = etree.XML(res['arch'])
        #~ if group_id:
            #~ if view_type == 'tree':
                #~ nodes = doc.xpath("//tree[@string='Test Tree']")
                #~ for node in nodes:
                    #~ node.set('create', '0')
                #~ res['arch'] = etree.tostring(doc)
        #~ return res

    @api.model
    def _search_new_account_code(self, company, digits, prefix):
        for num in range(1, 10000):
            new_code = str(prefix.ljust(digits - 1, '0')) + str(num)
            rec = self.search([('code', '=', new_code), ('company_id', '=', company.id)], limit=1)
            if not rec:
                return new_code
        raise UserError(_('Cannot generate an unused account code.'))

    def _compute_opening_debit_credit(self):
        for record in self:
            opening_debit = opening_credit = 0.0
            if record.company_id.account_opening_move_id:
                for line in self.env['account.move.line'].search([('account_id', '=', record.id),
                                                                 ('move_id','=', record.company_id.account_opening_move_id.id)]):
                    #could be executed at most twice: once for credit, once for debit
                    if line.debit:
                        opening_debit = line.debit
                    elif line.credit:
                        opening_credit = line.credit
            record.opening_debit = opening_debit
            record.opening_credit = opening_credit

    def _set_opening_debit(self):
        self._set_opening_debit_credit(self.opening_debit, 'debit')

    def _set_opening_credit(self):
        self._set_opening_debit_credit(self.opening_credit, 'credit')

    def _set_opening_debit_credit(self, amount, field):
        """ Generic function called by both opening_debit and opening_credit's
        inverse function. 'Amount' parameter is the value to be set, and field
        either 'debit' or 'credit', depending on which one of these two fields
        got assigned.
        """
        opening_move = self.company_id.account_opening_move_id

        if not opening_move:
            raise UserError(_("You must first define an opening move."))

        if opening_move.state == 'draft':
            # check whether we should create a new move line or modify an existing one
            opening_move_line = self.env['account.move.line'].search([('account_id', '=', self.id),
                                                                      ('move_id','=', opening_move.id),
                                                                      (field,'!=', False),
                                                                      (field,'!=', 0.0)]) # 0.0 condition important for import

            counter_part_map = {'debit': opening_move_line.credit, 'credit': opening_move_line.debit}
            # No typo here! We want the credit value when treating debit and debit value when treating credit

            if opening_move_line:
                if amount:
                    # modify the line
                    opening_move_line.with_context(check_move_validity=False)[field] = amount
                elif counter_part_map[field]:
                    # delete the line (no need to keep a line with value = 0)
                    opening_move_line.with_context(check_move_validity=False).unlink()
            elif amount:
                # create a new line, as none existed before
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'name': _('Opening balance'),
                        field: amount,
                        'move_id': opening_move.id,
                        'account_id': self.id,
                })

            # Then, we automatically balance the opening move, to make sure it stays valid
            if not 'import_file' in self.env.context:
                # When importing a file, avoid recomputing the opening move for each account and do it at the end, for better performances
                self.company_id._auto_balance_opening_move()

    @api.model
    def default_get(self, default_fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """
        default_name = self._context.get('default_name')
        default_code = self._context.get('default_code')
        if default_name and not default_code:
            try:
                default_code = int(default_name)
            except ValueError:
                pass
            if default_code:
                default_name = False
        contextual_self = self.with_context(default_name=default_name, default_code=default_code)
        return super(AccountAccount, contextual_self).default_get(default_fields)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        account_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(account_ids).name_get()

    @api.onchange('internal_type')
    def onchange_internal_type(self):
        self.reconcile = self.internal_type in ('receivable', 'payable')
        if self.internal_type == 'liquidity':
            self.reconcile = False

    @api.onchange('code')
    def onchange_code(self):
        AccountGroup = self.env['account.group']

        group = False
        code_prefix = self.code

        # find group with longest matching prefix
        while code_prefix:
            matching_group = AccountGroup.search([('code_prefix', '=', code_prefix)], limit=1)
            if matching_group:
                group = matching_group
                break
            code_prefix = code_prefix[:-1]
        self.group_id = group

    @api.multi
    def name_get(self):
        result = []
        for account in self:
            name = account.code + ' ' + account.name
            result.append((account.id, name))
        return result

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if default.get('code', False):
            return super(AccountAccount, self).copy(default)
        try:
            default['code'] = (str(int(self.code) + 10) or '')
            default.setdefault('name', _("%s (copy)") % (self.name or ''))
            while self.env['account.account'].search([('code', '=', default['code']),
                                                      ('company_id', '=', default.get('company_id', False) or self.company_id.id)], limit=1):
                default['code'] = (str(int(default['code']) + 10) or '')
                default['name'] = _("%s (copy)") % (self.name or '')
        except ValueError:
            default['code'] = _("%s (copy)") % (self.code or '')
            default['name'] = self.name
        return super(AccountAccount, self).copy(default)

    @api.model
    def load(self, fields, data):
        """ Overridden for better performances when importing a list of account
        with opening debit/credit. In that case, the auto-balance is postpone
        until the whole file has been imported.
        """
        rslt = super(AccountAccount, self).load(fields, data)

        if 'import_file' in self.env.context:
            companies = self.search([('id', 'in', rslt['ids'])]).mapped('company_id')
            for company in companies:
                company._auto_balance_opening_move()
        return rslt

    def _toggle_reconcile_to_true(self):
        '''Toggle the `reconcile´ boolean from False -> True

        Note that: lines with debit = credit = amount_currency = 0 are set to `reconciled´ = True
        '''
        if not self.ids:
            return None
        query = """
            UPDATE account_move_line SET
                reconciled = CASE WHEN debit = 0 AND credit = 0 AND amount_currency = 0
                    THEN true ELSE false END,
                amount_residual = (debit-credit),
                amount_residual_currency = amount_currency
            WHERE full_reconcile_id IS NULL and account_id IN %s
        """
        self.env.cr.execute(query, [tuple(self.ids)])

    def _toggle_reconcile_to_false(self):
        '''Toggle the `reconcile´ boolean from True -> False

        Note that it is disallowed if some lines are partially reconciled.
        '''
        if not self.ids:
            return None
        partial_lines_count = self.env['account.move.line'].search_count([
            ('account_id', 'in', self.ids),
            ('full_reconcile_id', '=', False),
            ('|'),
            ('matched_debit_ids', '!=', False),
            ('matched_credit_ids', '!=', False),
        ])
        if partial_lines_count > 0:
            raise UserError(_('You cannot switch an account to prevent the reconciliation '
                              'if some partial reconciliations are still pending.'))
        query = """
            UPDATE account_move_line
                SET amount_residual = 0, amount_residual_currency = 0
            WHERE full_reconcile_id = NULL AND account_id IN %s
        """
        self.env.cr.execute(query, [tuple(self.ids)])



    @api.multi
    def write(self, vals):
        # Do not allow changing the company_id when account_move_line already exist
        if vals.get('company_id', False):
            move_lines = self.env['account.move.line'].search([('account_id', 'in', self.ids)], limit=1)
            for account in self:
                if (account.company_id.id != vals['company_id']) and move_lines:
                    raise UserError(_('You cannot change the owner company of an account that already contains journal items.'))
        if 'reconcile' in vals:
            if vals['reconcile']:
                self.filtered(lambda r: not r.reconcile)._toggle_reconcile_to_true()
            else:
                self.filtered(lambda r: r.reconcile)._toggle_reconcile_to_false()
        if vals.get('currency_id'):
            for account in self:
                if self.env['account.move.line'].search_count([('account_id', '=', account.id), ('currency_id', 'not in', (False, vals['currency_id']))]):
                    raise UserError(_('You cannot set a currency on this account as it already has some journal entries having a different foreign currency.'))
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        if 'company_ids' in vals and vals['company_ids']:
            company_ids = vals['company_ids']
            print('SDDDDDDDDDDDDDSDDDDDDDDDD:',company_ids[0][2])
            code = self.code 
            if 'code' in vals:
                code = vals['code']
            for old_com in self.company_ids.ids:
                if old_com not in company_ids[0][2]:
                    for company in self.env['res.company'].browse(old_com):
                        if company.parent_id.id:
                            print('Company:',company)
#                             self.delete_coa(code, company.id)
                            self._cr.execute("select id from account_account where code=%s and company_id=%s", (code, company.id,))
                            res = self.env.cr.dictfetchall()
                            for account in res:
                                acc=account['id']
                                self.browse(acc).unlink()
        return super(AccountAccount, self).write(vals)

    @api.multi
    def unlink(self):
        if self.env['account.move.line'].search([('account_id', 'in', self.ids)], limit=1):
            raise UserError(_('You cannot perform this action on an account that contains journal items.'))
        #Checking whether the account is set as a property to any Partner or not
        values = ['account.account,%s' % (account_id,) for account_id in self.ids]
        partner_prop_acc = self.env['ir.property'].search([('value_reference', 'in', values)], limit=1)
        if partner_prop_acc:
            raise UserError(_('You cannot remove/deactivate an account which is set on a customer or vendor.'))
        return super(AccountAccount, self).unlink()

    @api.multi
    def mark_as_reconciled(self):
        return self.write({'last_time_entries_checked': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

    @api.multi
    def action_open_reconcile(self):
        self.ensure_one()
        # Open reconciliation view for this account
        if self.internal_type == 'payable':
            action_context = {'show_mode_selector': False, 'mode': 'suppliers'}
        elif self.internal_type == 'receivable':
            action_context = {'show_mode_selector': False, 'mode': 'customers'}
        else:
            action_context = {'show_mode_selector': False, 'mode': 'accounts', 'account_ids': [self.id,]}
        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }
