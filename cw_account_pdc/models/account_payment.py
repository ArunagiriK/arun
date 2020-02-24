# -*- encoding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.register.payments"

    effective_date = fields.Date('Effective Date', copy=False, default=False)
    cheque_date = fields.Date('Cheque Date', copy=False, default=False)
    related_journal = fields.Many2one('account.journal',
                                      string='Related Journal')

    def get_payments_vals(self):
        res = super(AccountRegisterPayment, self).get_payments_vals()
        if self.payment_method_id == self.env.ref('account_check_printing.account_payment_method_check') or self.payment_method_code == 'pdc':
            for rec in res:
                rec.update({
                    'cheque_date': self.cheque_date,
                    'related_journal': self.related_journal and self.related_journal.id or False
                })
        return res



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    effective_date = fields.Date('Effective Date', copy=False, default=False)
    related_journal = fields.Many2one('account.journal',
                                      string='Related Journal')
    pdc_reconciled = fields.Boolean(copy=False, string='Pdc Reconciled')
    pdc_manual_payment = fields.Boolean(compute='_compute_pdc_type',
                                        copy=False,
                                        string='Display PDC Payment Button')
    cheque_date = fields.Date('Cheque Date', copy=False, default=False)
    cheque_clear = fields.Boolean('Check cleared?')
    cheque_move_line_ids = fields.One2many('account.move.line', 'cheque_payment_id', readonly=True, copy=False, ondelete='restrict')

    @api.multi
    def action_pdc(self):
        '''
        This will open a pop up where you can update effective date.
        '''
        for rec in self:
            view_id = self.env.ref(
                'cw_account_pdc.wiz_view_account_pdc_form')
            return {
                'name': 'Account pdc Payment ',
                'type': 'ir.actions.act_window',
                'view_id': view_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wiz.pdc.payment',
                'target': 'new',
            }

    @api.depends()
    def _compute_pdc_type(self):
        '''
        sets pdc payment button true when pdc_type in account settings is set
        manual.
        '''
        account_pdc_type = self.company_id.pdc_type
        if not self.pdc_reconciled:
            if account_pdc_type == 'manual':
                self.pdc_manual_payment = True

    @api.model
    def account_pdc(self):
        '''
            This is scheduler method, will search Payments which in which
            Payment method is PDC and effective date is equal to today than it
            will create PDC JE and reconcile PDC entries.
        '''
        account_pdc_type = self.company_id.pdc_type == 'automatic'
        if account_pdc_type:
            rec = self.search([('cheque_date', '=',
                                datetime.today().date()),
                               ('pdc_reconciled', '=', False),
                               ('payment_method_code', '=', 'pdc')])
            self.create_move(rec)

    @api.multi
    def post(self):
        '''
            This method will check Payment method is PDC and effective date is
            less or equal to today than it will create PDC JE and reconcile PDC
            entries.
        '''
        res = super(AccountPayment, self).post()
        for rec in self:
            if rec.payment_method_code == 'pdc':
                if rec.cheque_date <= datetime.today().date():
                    return res

    @api.multi
    def create_move(self, res):
        '''
        This method will create JE for PDC and also reconcile PDC entries.
        '''
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        for rec in res:
            if rec.partner_type == 'customer':
                mv1_debit = rec.amount
                mv1_credit = 0.0
                mv2_debit = 0.0
                mv2_credit = rec.amount

            if rec.partner_type == 'supplier':
                mv1_debit = 0.0
                mv1_credit = rec.amount
                mv2_debit = rec.amount
                mv2_credit = 0.0

            move_line_1 = {
                'account_id':
                    rec.related_journal.default_debit_account_id.id,
                'name': '/',
                'debit': mv1_debit,
                'credit': mv1_credit,
                'company_id': rec.company_id.id,
                'date_maturity': rec.effective_date and rec.effective_date or rec.cheque_date,
                'cheque_payment_id': rec.id,
            }
            move_line_2 = {
                'account_id': rec.journal_id.default_credit_account_id.id,
                'name': rec.check_number,
                'credit': mv2_credit,
                'debit': mv2_debit,
                'company_id': rec.company_id.id,
                'date_maturity': rec.effective_date and rec.effective_date or rec.cheque_date,
                'cheque_payment_id': rec.id,
            }
            move = account_move_obj.create({
                'journal_id': rec.related_journal.id,
                'date': rec.effective_date and rec.effective_date or rec.cheque_date,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                'ref': rec.check_number
            })
            move.post()
            rec.state = 'posted'
            # search move lines of PDC, to reconcile
            if rec.partner_type == 'customer':
                move_lines = account_move_line_obj.search([
                    ('move_id', '=', move.id),
                    ('credit', '!=', 0.0)])
                move_lines += account_move_line_obj.search([
                    ('payment_id', '=', rec.id),
                    ('debit', '!=', 0.0)])
            if rec.partner_type == 'supplier':
                move_lines = account_move_line_obj.search([
                    ('move_id', '=', move.id),
                    ('debit', '!=', 0.0)])
                move_lines += account_move_line_obj.search([
                    ('payment_id', '=', rec.id),
                    ('credit', '!=', 0.0)])
            # reconcile move lines
            move_lines_filtered = move_lines.filtered(
                lambda aml: not aml.reconciled)
            move_lines_filtered.with_context(
                skip_full_reconcile_check='amount_currency_excluded'
            ).reconcile()
            move_lines.check_full_reconcile()
            rec.pdc_reconciled = True

    @api.multi
    def cheque_bounce(self):
        '''
         This will raise warning if effective date is greater than current date
         else it will unlink move and set state as draft.
        '''
        for payment_rec in self:
            if payment_rec.cheque_date > datetime.today().date():
                raise ValidationError(_(
                    "Check can not bounced before Cheque date!"))
            payment_rec.cancel()
            payment_rec.state = 'draft'

    @api.multi
    def cancel(self):
        for rec in self:
            for move in rec.move_line_ids.mapped('move_id'):
#                 if rec.invoice_ids:
                move.line_ids.remove_move_reconcile()
                move.button_cancel()
                move.unlink()
            for cheque_move in rec.cheque_move_line_ids.mapped('move_id'):
                cheque_move.line_ids.remove_move_reconcile()
                cheque_move.button_cancel()
                cheque_move.unlink()
            if rec.cheque_clear:
                rec.cheque_clear = False
            rec.state = 'cancelled'

#     @api.multi
#     def cancel(self):
#         res = super(AccountPayment, self).cancel()
#         if self.cheque_clear:
#             self.cheque_clear = False
#         return res


    @api.multi
    def button_check_journal_entries(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('cheque_payment_id', 'in', self.ids)],
        }



class MoveLine(models.Model):

    _inherit = 'account.move.line'

    cheque_payment_id = fields.Many2one('account.payment', string = 'Payment')
