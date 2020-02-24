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

#----------------------------------------------------------
# Entries
#----------------------------------------------------------



class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Journal Entries"
    _order = 'date desc, id desc'

    @api.multi
    @api.depends('name', 'state')
    def name_get(self):
        result = []
        for move in self:
            if move.state == 'draft':
                name = '* ' + str(move.id)
            else:
                name = move.name
            result.append((move.id, name))
        return result

    @api.multi
    @api.depends('line_ids.debit', 'line_ids.credit')
    def _amount_compute(self):
        for move in self:
            total = 0.0
            for line in move.line_ids:
                total += line.debit
            move.amount = total

    @api.depends('line_ids.debit', 'line_ids.credit', 'line_ids.matched_debit_ids.amount', 'line_ids.matched_credit_ids.amount', 'line_ids.account_id.user_type_id.type')
    def _compute_matched_percentage(self):
        """Compute the percentage to apply for cash basis method. This value is relevant only for moves that
        involve journal items on receivable or payable accounts.
        """
        for move in self:
            total_amount = 0.0
            total_reconciled = 0.0
            for line in move.line_ids:
                if line.account_id.user_type_id.type in ('receivable', 'payable'):
                    amount = abs(line.debit - line.credit)
                    total_amount += amount
            precision_currency = move.currency_id or move.company_id.currency_id
            if float_is_zero(total_amount, precision_rounding=precision_currency.rounding):
                move.matched_percentage = 1.0
            else:
                for line in move.line_ids:
                    if line.account_id.user_type_id.type in ('receivable', 'payable'):
                        for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
                            total_reconciled += partial_line.amount
                move.matched_percentage = total_reconciled / total_amount

    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id 

    @api.multi
    def _get_default_journal(self):
        if self.env.context.get('default_journal_type'):
            return self.env['account.journal'].search([('type', '=', self.env.context['default_journal_type'])], limit=1).id

    @api.multi
    @api.depends('line_ids.partner_id')
    def _compute_partner_id(self):
        for move in self:
            partner = move.line_ids.mapped('partner_id')
            move.partner_id = partner.id if len(partner) == 1 else False

    @api.onchange('date')
    def _onchange_date(self):
        '''On the form view, a change on the date will trigger onchange() on account.move
        but not on account.move.line even the date field is related to account.move.
        Then, trigger the _onchange_amount_currency manually.
        '''
        self.line_ids._onchange_amount_currency()

    name = fields.Char(string='Number', required=True, copy=False, default='/')
    ref = fields.Char(string='Reference', copy=False)
    date = fields.Date(required=True, states={'posted': [('readonly', True)]}, index=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, states={'posted': [('readonly', True)]}, default=_get_default_journal)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, string="Currency")
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status',
      required=True, readonly=True, copy=False, default='draft',
      help='All manually created new journal entries are usually in the status \'Unposted\', '
           'but you can set the option to skip that status on the related journal. '
           'In that case, they will behave as journal entries automatically created by the '
           'system on document validation (invoices, bank statements...) and will be created '
           'in \'Posted\' status.')
    line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items',
        states={'posted': [('readonly', True)]}, copy=True)
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', string="Partner", store=True, readonly=True)
    amount = fields.Monetary(compute='_amount_compute', store=True)
    narration = fields.Text(string='Internal Note')
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True, readonly=True)
    matched_percentage = fields.Float('Percentage Matched', compute='_compute_matched_percentage', digits=0, store=True, readonly=True, help="Technical field used in cash basis method")
    # Dummy Account field to search on account.move by account_id
    dummy_account_id = fields.Many2one('account.account', related='line_ids.account_id', string='Account', store=False, readonly=True)
    tax_cash_basis_rec_id = fields.Many2one(
        'account.partial.reconcile',
        string='Tax Cash Basis Entry of',
        help="Technical field used to keep track of the tax cash basis reconciliation. "
        "This is needed when cancelling the source: it will post the inverse journal entry to cancel that part too.")
    auto_reverse = fields.Boolean(string='Reverse Automatically', default=False, help='If this checkbox is ticked, this entry will be automatically reversed at the reversal date you defined.')
    reverse_date = fields.Date(string='Reversal Date', help='Date of the reverse accounting entry.')
    reverse_entry_id = fields.Many2one('account.move', String="Reverse entry", store=True, readonly=True, copy=False)
    tax_type_domain = fields.Char(store=False, help='Technical field used to have a dynamic taxes domain on the form view.')

    @api.constrains('line_ids', 'journal_id', 'auto_reverse', 'reverse_date')
    def _validate_move_modification(self):
        if 'posted' in self.mapped('line_ids.payment_id.state'):
            raise ValidationError(_("You cannot modify a journal entry linked to a posted payment."))

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.tax_type_domain = self.journal_id.type if self.journal_id.type in ('sale', 'purchase') else None

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        company_id = []
        for company_obj in self.env['res.company'].search([]):
            if company_obj.parent_id.id:
                company_id.append(company_obj.id)
        child_company = self.env.context.get('child_company', False)
        parent_company = self.env.context.get('parent_company', False)
        if child_company == 'yes':
            args += [('company_id', '=', company_id)]
            print('Child:',args)
        elif parent_company == 'yes':
            args += [('company_id', '!=', company_id)]
        return super(AccountMove, self).search(args, offset, limit, order, count=count)

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        '''Compute additional lines corresponding to the taxes set on the line_ids.

        For example, add a line with 1000 debit and 15% tax, this onchange will add a new
        line with 150 debit.
        '''
        def _str_to_list(string):
            #remove heading and trailing brackets and return a list of int. This avoid calling safe_eval on untrusted field content
            string = string[1:-1]
            if string:
                return [int(x) for x in string.split(',')]
            return []

        def _build_grouping_key(line):
            #build a string containing all values used to create the tax line
            return str(line.tax_ids.ids) + '-' + str(line.analytic_tag_ids.ids) + '-' + (line.analytic_account_id and str(line.analytic_account_id.id) or '')

        def _parse_grouping_key(line):
            # Retrieve values computed the last time this method has been run.
            if not line.tax_line_grouping_key:
                return {'tax_ids': [], 'tag_ids': [], 'analytic_account_id': False}
            tax_str, tags_str, analytic_account_str = line.tax_line_grouping_key.split('-')
            return {
                'tax_ids': _str_to_list(tax_str),
                'tag_ids': _str_to_list(tags_str),
                'analytic_account_id': analytic_account_str and int(analytic_account_str) or False,
            }

        def _find_existing_tax_line(line_ids, tax, tag_ids, analytic_account_id):
            if tax.analytic:
                return line_ids.filtered(lambda x: x.tax_line_id == tax and x.analytic_tag_ids.ids == tag_ids and x.analytic_account_id.id == analytic_account_id)
            return line_ids.filtered(lambda x: x.tax_line_id == tax)

        def _get_lines_to_sum(line_ids, tax, tag_ids, analytic_account_id):
            if tax.analytic:
                return line_ids.filtered(lambda x: tax in x.tax_ids and x.analytic_tag_ids.ids == tag_ids and x.analytic_account_id.id == analytic_account_id)
            return line_ids.filtered(lambda x: tax in x.tax_ids)

        def _get_tax_account(tax, amount):
            if tax.tax_exigibility == 'on_payment' and tax.cash_basis_account_id:
                return tax.cash_basis_account_id
            if tax.type_tax_use == 'purchase':
                return tax.refund_account_id if amount < 0 else tax.account_id
            return tax.refund_account_id if amount >= 0 else tax.account_id

        # Cache the already computed tax to avoid useless recalculation.
        processed_taxes = self.env['account.tax']

        self.ensure_one()
        for line in self.line_ids.filtered(lambda x: x.recompute_tax_line):
            # Retrieve old field values.
            parsed_key = _parse_grouping_key(line)

            # Unmark the line.
            line.recompute_tax_line = False

            # Manage group of taxes.
            group_taxes = line.tax_ids.filtered(lambda t: t.amount_type == 'group')
            children_taxes = group_taxes.mapped('children_tax_ids')
            if children_taxes:
                line.tax_ids += children_taxes - line.tax_ids
                # Because the taxes on the line changed, we need to recompute them.
                processed_taxes -= children_taxes

            # Get the taxes to process.
            taxes = self.env['account.tax'].browse(parsed_key['tax_ids'])
            taxes += line.tax_ids.filtered(lambda t: t not in taxes)
            taxes += children_taxes.filtered(lambda t: t not in taxes)
            to_process_taxes = (taxes - processed_taxes).filtered(lambda t: t.amount_type != 'group')
            processed_taxes += to_process_taxes

            # Process taxes.
            for tax in to_process_taxes:
                tax_line = _find_existing_tax_line(self.line_ids, tax, parsed_key['tag_ids'], parsed_key['analytic_account_id'])
                lines_to_sum = _get_lines_to_sum(self.line_ids, tax, parsed_key['tag_ids'], parsed_key['analytic_account_id'])

                if not lines_to_sum:
                    # Drop tax line because the originator tax is no longer used.
                    self.line_ids -= tax_line
                    continue

                balance = sum([l.balance for l in lines_to_sum])

                # Compute the tax amount one by one.
                quantity = len(lines_to_sum) if tax.amount_type == 'fixed' else 1
                taxes_vals = tax.compute_all(balance,
                    quantity=quantity, currency=line.currency_id, product=line.product_id, partner=line.partner_id)

                if tax_line:
                    # Update the existing tax_line.
                    if balance:
                        # Update the debit/credit amount according to the new balance.
                        if taxes_vals.get('taxes'):
                            amount = taxes_vals['taxes'][0]['amount']
                            account = _get_tax_account(tax, amount) or line.account_id
                            tax_line.debit = amount > 0 and amount or 0.0
                            tax_line.credit = amount < 0 and -amount or 0.0
                            tax_line.account_id = account
                    else:
                        # Reset debit/credit in case of the originator line is temporary set to 0 in both debit/credit.
                        tax_line.debit = tax_line.credit = 0.0
                elif taxes_vals.get('taxes'):
                    # Create a new tax_line.

                    amount = taxes_vals['taxes'][0]['amount']
                    account = _get_tax_account(tax, amount) or line.account_id
                    tax_vals = taxes_vals['taxes'][0]

                    name = tax_vals['name']
                    line_vals = {
                        'account_id': account.id,
                        'name': name,
                        'tax_line_id': tax_vals['id'],
                        'partner_id': line.partner_id.id,
                        'debit': amount > 0 and amount or 0.0,
                        'credit': amount < 0 and -amount or 0.0,
                        'analytic_account_id': line.analytic_account_id.id if tax.analytic else False,
                        'analytic_tag_ids': line.analytic_tag_ids.ids if tax.analytic else False,
                        'move_id': self.id,
                        'tax_exigible': tax.tax_exigibility == 'on_invoice',
                        'company_id': self.company_id.id,
                        'company_currency_id': self.company_id.currency_id.id,
                    }
                    # N.B. currency_id/amount_currency are not set because if we have two lines with the same tax
                    # and different currencies, we have no idea which currency set on this line.
                    self.env['account.move.line'].new(line_vals)

            # Keep record of the values used as taxes the last time this method has been run.
            line.tax_line_grouping_key = _build_grouping_key(line)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('vat_domain'):
            res['fields']['line_ids']['views']['tree']['fields']['tax_line_id']['domain'] = [('tag_ids', 'in', [self.env.ref(self._context.get('vat_domain')).id])]
        return res

    @api.model
    def create(self, vals):
        move = super(AccountMove, self.with_context(check_move_validity=False, partner_id=vals.get('partner_id'))).create(vals)
        move.assert_balanced()
        return move

    @api.multi
    def write(self, vals):
        if 'line_ids' in vals:
            res = super(AccountMove, self.with_context(check_move_validity=False)).write(vals)
            self.assert_balanced()
        else:
            res = super(AccountMove, self).write(vals)
        return res

    @api.multi
    def post(self, invoice=False):
        self._post_validate()
        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped('line_ids').create_analytic_lines()
        for move in self:
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(_('Please define a sequence for the credit notes'))
                            sequence = journal.refund_sequence_id

                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name

            if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
                # For opening moves, we set the reconciliation date threshold
                # to the move's date if it wasn't already set (we don't want
                # to have to reconcile all the older payments -made before
                # installing Accounting- with bank statements)
                move.company_id.account_bank_reconciliation_start = move.date

        return self.write({'state': 'posted'})

    @api.multi
    def action_post(self):
        if self.mapped('line_ids.payment_id'):
            if any(self.mapped('journal_id.post_at_bank_rec')):
                raise UserError(_("A payment journal entry generated in a journal configured to post entries only when payments are reconciled with a bank statement cannot be manually posted. Those will be posted automatically after performing the bank reconciliation."))
        return self.post()

    @api.multi
    def button_cancel(self):
        for move in self:
            if not move.journal_id.update_posted:
                raise UserError(_('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
            # We remove all the analytics entries for this journal
            move.mapped('line_ids.analytic_line_ids').unlink()
        if self.ids:
            self.check_access_rights('write')
            self.check_access_rule('write')
            self._check_lock_date()
            self._cr.execute('UPDATE account_move '\
                       'SET state=%s '\
                       'WHERE id IN %s', ('draft', tuple(self.ids),))
            self.invalidate_cache()
        self._check_lock_date()
        return True

    @api.multi
    def unlink(self):
        for move in self:
            #check the lock date + check if some entries are reconciled
            move.line_ids._update_check()
            move.line_ids.unlink()
        return super(AccountMove, self).unlink()

    @api.multi
    def _post_validate(self):
        for move in self:
            #~ if move.line_ids:
                #~ if not all([x.company_id.id == move.company_id.id for x in move.line_ids]):
                    #~ raise UserError(_("Cannot create moves for different companies."))
           self.assert_balanced()
        return self._check_lock_date()

    @api.multi
    def _check_lock_date(self):
        for move in self:
            lock_date = max(move.company_id.period_lock_date or date.min, move.company_id.fiscalyear_lock_date or date.min)
            if self.user_has_groups('account.group_account_manager'):
                lock_date = move.company_id.fiscalyear_lock_date
            if move.date <= (lock_date or date.min):
                if self.user_has_groups('account.group_account_manager'):
                    message = _("You cannot add/modify entries prior to and inclusive of the lock date %s") % (lock_date)
                else:
                    message = _("You cannot add/modify entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Adviser' role") % (lock_date)
                raise UserError(message)
        return True

    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        res = self._cr.fetchone()
        if res:
            raise UserError(
                _("Cannot create unbalanced journal entry.") +
                "\n\n{}{}".format(_('Difference debit - credit: '), res[1])
            )
        return True

    @api.multi
    def _reverse_move(self, date=None, journal_id=None, auto=False):
        self.ensure_one()
        date = date or fields.Date.today()
        with self.env.norecompute():
            reversed_move = self.copy(default={
                'date': date,
                'journal_id': journal_id.id if journal_id else self.journal_id.id,
                'ref': (_('Automatic reversal of: %s') if auto else _('Reversal of: %s')) % (self.name),
                'auto_reverse': False})
            for acm_line in reversed_move.line_ids.with_context(check_move_validity=False):
                acm_line.write({
                    'debit': acm_line.credit,
                    'credit': acm_line.debit,
                    'amount_currency': -acm_line.amount_currency
                })
            self.reverse_entry_id = reversed_move
        self.recompute()
        return reversed_move

    @api.multi
    def reverse_moves(self, date=None, journal_id=None, auto=False):
        date = date or fields.Date.today()
        reversed_moves = self.env['account.move']
        for ac_move in self:
            #unreconcile all lines reversed
            aml = ac_move.line_ids.filtered(lambda x: x.account_id.reconcile or x.account_id.internal_type == 'liquidity')
            aml.remove_move_reconcile()
            reversed_move = ac_move._reverse_move(date=date,
                                                  journal_id=journal_id,
                                                  auto=auto)
            reversed_moves |= reversed_move
            #reconcile together the reconcilable (or the liquidity aml) and their newly created counterpart
            for account in set([x.account_id for x in aml]):
                to_rec = aml.filtered(lambda y: y.account_id == account)
                to_rec |= reversed_move.line_ids.filtered(lambda y: y.account_id == account)
                #reconciliation will be full, so speed up the computation by using skip_full_reconcile_check in the context
                to_rec.reconcile()
        if reversed_moves:
            reversed_moves._post_validate()
            reversed_moves.post()
            return [x.id for x in reversed_moves]
        return []

    @api.multi
    def open_reconcile_view(self):
        return self.line_ids.open_reconcile_view()

    # FIXME: Clarify me and change me in master
    @api.multi
    def action_duplicate(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['context'] = dict(self.env.context)
        action['context']['form_view_initial_mode'] = 'edit'
        action['context']['view_no_maturity'] = False
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = self.copy().id
        return action

    @api.model
    def _run_reverses_entries(self):
        ''' This method is called from a cron job. '''
        records = self.search([
            ('state', '=', 'posted'),
            ('auto_reverse', '=', True),
            ('reverse_date', '<=', fields.Date.today()),
            ('reverse_entry_id', '=', False)])
        for move in records:
            date = None
            company = move.company_id or self.env.user.company_id
            if move.reverse_date and (not company.period_lock_date or move.reverse_date > company.period_lock_date):
                date = move.reverse_date
            move.reverse_moves(date=date, auto=True)

    @api.multi
    def action_view_reverse_entry(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = self.reverse_entry_id.id
        return action




