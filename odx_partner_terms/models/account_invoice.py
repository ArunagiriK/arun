from datetime import date,datetime
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    term_id = fields.Many2one('partner.term.calculation', string='Term')
    partner_term_value = fields.Float('Term Value')

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if self.partner_id:
            if self.partner_id.partner_terms_ids:
                for partner_term in self.partner_id.partner_terms_ids:
                    if partner_term.terms_id:
                        credit_value = partner_term.terms_id._get_term_value(partner=self.partner_id,invoice=self)
                        for record in partner_term.terms_id:
                            if record.create_type=='credit_note':
                                if record and record.active \
                                        and (self.id not in record.history_invoice_ids.ids) \
                                        and record.term_calculation_type=='on_invoice':
                                    if record.periodic_terms:
                                        from_date = datetime.strptime(str(partner_term.invoice_from_date),
                                                                      '%Y-%m-%d').date()
                                        to_date = datetime.strptime(str(partner_term.invoice_to_date),
                                                                    '%Y-%m-%d').date()
                                        if (from_date < date.today()) \
                                            and (to_date > date.today()):
                                            if credit_value:
                                                self.term_id = record.id
                                                self.partner_term_value = credit_value

                                                if not record.partner_term_product_id.property_account_income_id:
                                                    raise ValidationError('No Account is defined for '
                                                                          'the Product associated with partner term')
                                                credit_invoice = self.env['account.invoice'].create(
                                                    {'partner_id': self.partner_id.id,
                                                     'type': 'out_refund',
                                                     'journal_id':record.partner_term_journal_id.id}
                                                )
                                                invoice_lines={'product_id': record.partner_term_product_id.id,
                                                     'name':record.name,
                                                     'account_id':record.partner_term_product_id.property_account_income_id.id,
                                                     'price_unit': credit_value,
                                                     'invoice_line_tax_ids':[(6,0,record.partner_term_product_id.taxes_id.ids)],
                                                     'invoice_id': credit_invoice.id}
                                                self.env['account.invoice.line'].create(invoice_lines)
                                                return credit_invoice._onchange_invoice_line_ids()
                                    else:
                                        if credit_value:
                                            self.term_id = record.id
                                            self.partner_term_value = credit_value

                                            if not record.partner_term_product_id.property_account_income_id:
                                                raise ValidationError('No Account is defined for '
                                                                      'the Product associated with partner term')

                                            credit_invoice = self.env['account.invoice'].create(
                                                {'partner_id': self.partner_id.id,
                                                 'type': 'out_refund',
                                                 'journal_id': record.partner_term_journal_id.id}
                                            )
                                            invoice_line = self.env['account.invoice.line'].create(
                                                {'product_id': record.partner_term_product_id.id,
                                                 'name': record.name,
                                                 'account_id': record.partner_term_product_id.property_account_income_id.id,
                                                 'price_unit': credit_value,
                                                 'invoice_line_tax_ids':[(6,0,record.partner_term_product_id.taxes_id.ids)],
                                                 'invoice_id': credit_invoice.id}
                                            )
                                            return credit_invoice._onchange_invoice_line_ids()

                            if record.create_type == 'journal':
                                if record and record.active \
                                        and (self.id not in record.history_invoice_ids.ids) \
                                        and record.term_calculation_type == 'on_invoice':
                                    if record.periodic_terms:
                                        from_date = datetime.strptime(str(partner_term.invoice_from_date),
                                                                      '%Y-%m-%d').date()
                                        to_date = datetime.strptime(str(partner_term.invoice_to_date),
                                                                    '%Y-%m-%d').date()
                                        if (from_date < date.today()) \
                                                and (to_date > date.today()):
                                            if credit_value:
                                                self.term_id = record.id
                                                self.partner_term_value = credit_value
                                                debit_line_vals = {
                                                    'partner_id':self.partner_id.id,
                                                    'name': record.name,
                                                    'debit': 0.0,
                                                    'credit': credit_value,
                                                    'account_id': record.credit_account_id.id,
                                                }
                                                credit_line_vals = {
                                                    'partner_id':self.partner_id.id,
                                                    'name': record.name,
                                                    'debit': credit_value,
                                                    'credit': 0.0,
                                                    'account_id': record.debit_account_id.id,
                                                }
                                                vals = {
                                                    'ref':self.number,
                                                    'journal_id': record.partner_term_journal_id.id,
                                                    'line_ids': [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
                                                }
                                                move_id = self.env['account.move'].create(vals)
                                                move_id.post()
                                    else:
                                        if credit_value:
                                            self.term_id = record.id
                                            self.partner_term_value = credit_value
                                            debit_line_vals = {
                                                'partner_id': self.partner_id.id,
                                                'name': record.name,
                                                'debit': 0.0,
                                                'credit': credit_value,
                                                'account_id': record.credit_account_id.id,
                                            }
                                            credit_line_vals = {
                                                'partner_id': self.partner_id.id,
                                                'name': record.name,
                                                'debit': credit_value,
                                                'credit': 0.0,
                                                'account_id': record.debit_account_id.id,
                                            }
                                            vals = {
                                                'ref': self.number,
                                                'journal_id': record.partner_term_journal_id.id,
                                                'line_ids': [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
                                            }
                                            move_id = self.env['account.move'].create(vals)
                                            move_id.post()
                            if record.create_type == 'vendor_bill':
                                if record and record.active \
                                        and (self.id not in record.history_invoice_ids.ids) \
                                        and record.term_calculation_type == 'on_invoice':
                                    if record.periodic_terms:
                                        from_date = datetime.strptime(str(partner_term.invoice_from_date),
                                                                      '%Y-%m-%d').date()
                                        to_date = datetime.strptime(str(partner_term.invoice_to_date),
                                                                    '%Y-%m-%d').date()
                                        if (from_date < date.today()) \
                                                and (to_date > date.today()):
                                            if credit_value:
                                                self.term_id = record.id
                                                self.partner_term_value = credit_value

                                                credit_invoice = self.env['account.invoice'].create(
                                                    {'partner_id': self.partner_id.id,
                                                     'type': 'in_invoice',
                                                     'journal_id': record.partner_term_journal_id.id}
                                                )
                                                self.env['account.invoice.line'].create(
                                                    {'product_id': record.partner_term_product_id.id,
                                                     'name': record.name,
                                                     'invoice_line_tax_ids': [
                                                         (6, 0, record.partner_term_product_id.taxes_id.ids)],
                                                     'account_id': record.partner_term_product_id.property_account_income_id.id,
                                                     'price_unit': credit_value,
                                                     'invoice_id': credit_invoice.id}
                                                )
                                    else:
                                        if credit_value:
                                            self.term_id = record.id
                                            self.partner_term_value = credit_value

                                            credit_invoice = self.env['account.invoice'].create(
                                                {'partner_id': self.partner_id.id,
                                                 'type': 'in_invoice',
                                                 'journal_id': record.partner_term_journal_id.id}
                                            )
                                            self.env['account.invoice.line'].create(
                                                {'product_id': record.partner_term_product_id.id,
                                                 'name': record.name,
                                                 'invoice_line_tax_ids': [
                                                     (6, 0, record.partner_term_product_id.taxes_id.ids)],
                                                 'account_id': record.partner_term_product_id.property_account_income_id.id,
                                                 'price_unit': credit_value,
                                                 'invoice_id': credit_invoice.id}
                                            )
        return res