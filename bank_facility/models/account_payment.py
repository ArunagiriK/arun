# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class account_payment(models.Model):
    _inherit = 'account.payment'

    bank_facility_id = fields.Many2one('bank.facility','Bank Facility')
    amount = fields.Float(string='Payment Amount')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'),('repayment','Repayment'),('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    bank_pay = fields.Boolean('Bank Facility')



    @api.onchange('bank_facility_id')
    def _onchange_bank_test(self):
        if self.bank_facility_id.journal_id:
            self.journal_id = self.bank_facility_id.journal_id.id
               
    @api.multi
    def action_repayment(self, date=None, account_payable=None, auto=False):
        if self.bank_facility_id:
           if self.bank_facility_id.faciltiy_type == 'od':
              for rec in self:
                  debit = credit = rec.currency_id.compute(rec.bank_facility_id.amount, rec.currency_id)
                  debit_amount = credit_amount = rec.currency_id.compute(rec.bank_facility_id.interest_percentage, rec.currency_id)
                  amount_interest = rec.amount * rec.bank_facility_id.interest_percentage / 100
                  bank_pay = rec.amount + amount_interest + rec.bank_facility_id.amount
                  move = {
                         'name': rec.communication or '/',
                         'journal_id': rec.journal_id.id,
                         'date': date,

                         'line_ids': [
                            (0, 0, {
                                 'name': rec.journal_id.name or ' ',
                                 'credit': bank_pay,
                                 'account_id': account_payable.id,
                                 'partner_id': rec.partner_id.id,
                             }),
                            (0, 0, {
                                     'name': rec.bank_facility_id.name or ' ',
                                     'debit': bank_pay,
                                     'account_id': rec.bank_facility_id.facility_account_payable.id,
                                     'partner_id': rec.partner_id.id,
                                 }),
                        ]
                     }
                  move_id = self.env['account.move'].sudo().create(move)
                  move_id.post()
                  rec.write({'state': 'repayment'})
                  return True
                  
            
    
    
    @api.multi
    def action_payment(self):
        if self.bank_facility_id:
           if self.bank_facility_id.faciltiy_type == 'od':
                 for rec in self:
                     if rec.company_id.parent_id:
                        total =  rec.company_id.faciltity_utilized_given + rec.amount 
                        rec.company_id.write({'faciltity_utilized_given':total})
                     debit = credit = rec.currency_id.compute(rec.bank_facility_id.amount, rec.currency_id)   
                     debit_amount = credit_amount = rec.currency_id.compute(rec.bank_facility_id.interest_percentage, rec.currency_id)
                     amount_interest = rec.amount * rec.bank_facility_id.interest_percentage / 100 
                     bank_pay = rec.amount + amount_interest + rec.bank_facility_id.amount
                     move = {
                         'name': rec.communication or '/',
                         'journal_id': rec.journal_id.id,
                         'date': rec.payment_date,
             
                         'line_ids': [
                            (0, 0, {
                                 'name': rec.bank_facility_id.name or '/',
                                 'credit': bank_pay,
                                 'account_id': rec.bank_facility_id.facility_account_payable.id,
                                 'partner_id': rec.partner_id.id,
                             }),
                            (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': debit,
                                     'account_id': rec.bank_facility_id.facility_interest_charges.id,
                                     'partner_id': rec.partner_id.id,
                                 }),
                            (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': amount_interest,
                                     'account_id': rec.bank_facility_id.facility_interest_charges.id,
                                     'partner_id': rec.partner_id.id,
                                 }),
                            (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': rec.amount,
                                     'account_id': rec.journal_id.default_debit_account_id.id,
                                     'partner_id': rec.partner_id.id,
                                 }),
                        ]
                     }
                     move_id = self.env['account.move'].sudo().create(move)
                     move_id.post()
                     return True
      
    
    #~ @api.multi
    #~ def action_amount(self):
        #~ for rec in self:
            #~ if rec.company_id.parent_id:
               #~ total =  rec.company_id.faciltity_utilized_given + rec.amount 
               #~ rec.company_id.write({'faciltity_utilized_given': total})

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:
            #~ if rec.state != 'draft':
                #~ raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)
            persist_move_name = move.name

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()
                persist_move_name += self._get_move_name_transfer_separator() + transfer_debit_aml.move_id.name

            rec.write({'state': 'posted', 'move_name': persist_move_name})
            self.action_payment()
        return True

     
        

    def action_validate_invoice_payment(self):
        """ Posts a payment used to pay an invoice. This function only posts the
        payment by default but can be overridden to apply specific post or pre-processing.
        It is called by the "validate" button of the popup window
        triggered on invoice form by the "Register Payment" button.
        """
        res = super(account_payment, self).action_validate_invoice_payment()
        #~ if any(len(record.invoice_ids) != 1 for record in self):
            #~ # For multiple invoices, there is account.register.payments wizard
            #~ raise UserError(_("This method should only be called to process a single invoice's payment."))
        self.action_done()
        return res

    @api.multi
    def action_done(self):
        if self.bank_facility_id:
            if self.bank_facility_id.faciltiy_type == 'od':
                for rec in self:
                    for invoice in rec.invoice_ids:
                         debit = credit = rec.currency_id.compute(rec.bank_facility_id.amount, rec.currency_id)   
                         debit_amount = credit_amount = rec.currency_id.compute(rec.bank_facility_id.interest_percentage, rec.currency_id)
                         amount_interest = rec.amount * rec.bank_facility_id.interest_percentage / 100 
                         bank_pay = rec.amount + amount_interest + rec.bank_facility_id.amount            
                         move = {
                             'name': '/',
                             'journal_id': rec.bank_facility_id.journal_id.id,
                             'date': invoice.date_invoice,
                 
                             'line_ids':[(0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'credit': bank_pay,
                                     'account_id': rec.bank_facility_id.facility_account_payable.id,
                                     'partner_id': invoice.partner_id.id,
                                 }), (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': debit,
                                     'account_id': rec.bank_facility_id.facility_interest_charges.id,
                                     'partner_id': invoice.partner_id.id,
                                 }),
                                 (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': amount_interest,
                                     'account_id': rec.bank_facility_id.facility_interest_charges.id,
                                     'partner_id': invoice.partner_id.id,
                                 }),
                                 (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': rec.amount,
                                     'account_id': rec.journal_id.default_debit_account_id.id,
                                     'partner_id': invoice.partner_id.id,
                                 })
                                ]
                         }
                         
                         move_id = self.env['account.move'].sudo().create(move)
                         move_id.post()    
                         return True
            if self.bank_facility_id.faciltiy_type != 'od':
                for rec in self:
                    for invoice in rec.invoice_ids:
                         debit = credit = rec.currency_id.compute(rec.bank_facility_id.charges_details, rec.currency_id)           
                         move = {
                             'name': '/',
                             'journal_id': rec.bank_facility_id.journal_id.id,
                             'date': invoice.date_invoice,
                 
                             'line_ids': [(0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'debit': debit,
                                     'account_id': rec.bank_facility_id.interest_details.id,
                                     'partner_id': invoice.partner_id.id,
                                 }), (0, 0, {
                                     'name': rec.bank_facility_id.name or '/',
                                     'credit': credit,
                                     'account_id': rec.bank_facility_id.interest_details.id,
                                     'partner_id': invoice.partner_id.id,
                                 })]
                         }
                         move_id = self.env['account.move'].sudo().create(move)
                         move_id.post() 
                         return True



class account_move(models.Model):
    _inherit = 'account.move'

    @api.constrains('line_ids', 'journal_id', 'auto_reverse', 'reverse_date')
    def _validate_move_modification(self):
        if 'repayment' in self.mapped('line_ids.payment_id.state'):
            raise ValidationError(_("You cannot modify a journal entry linked to a posted payment."))









    
