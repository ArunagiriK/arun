from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ResPartnerScheduleAction(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def automatic_function_call(self):
        partners = self.env['res.partner'].search([('customer', '=', True)])
        for partner in partners:
            if partner.partner_terms_ids:
                for partner_term in partner.partner_terms_ids:
                    if partner_term.terms_id:
                        for record in partner_term.terms_id:
                            if record and record.active and partner_term.invoice_from_date \
                                and partner_term.invoice_to_date and partner_term.term_calculation_type == 'automatic':
                                from_date = datetime.strptime(str(partner_term.invoice_from_date),
                                                              '%Y-%m-%d').date()
                                to_date = datetime.strptime(str(partner_term.invoice_to_date),
                                                            '%Y-%m-%d').date()

                                if (from_date < date.today()) and (to_date > date.today()):
                                    if record.frequency == 'only_once' and partner_term.execution_date:
                                        only_once_date = datetime.strptime(str(partner_term.execution_date),
                                                                           '%Y-%m-%d').date()
                                        if only_once_date == date.today():
                                            self.automatic_invoice_schedule_action(partner, record, partner_term)
                                    elif record.frequency == 'periodic' and partner_term.invoice_from_date \
                                            and partner_term.invoice_to_date:
                                        periodic_date = datetime.strptime(str(partner_term.execution_date),
                                                                          '%Y-%m-%d').date()
                                        if record.automatic_calculation_type == 'daily':
                                            if periodic_date == date.today():
                                                self.automatic_invoice_schedule_action(partner, record, partner_term)
                                                updated_date = periodic_date + relativedelta(days=1)
                                                partner_term.write({'execution_date': updated_date})
                                        if record.automatic_calculation_type == 'weekly':
                                            if periodic_date == date.today():
                                                self.automatic_invoice_schedule_action(partner, record, partner_term)
                                                updated_date = periodic_date + relativedelta(days=7)
                                                partner_term.write({'execution_date': updated_date})
                                        if record.automatic_calculation_type == 'monthly':
                                            if periodic_date == date.today():
                                                self.automatic_invoice_schedule_action(partner, record,partner_term)
                                                updated_date = periodic_date + relativedelta(months=1)
                                                partner_term.write({'execution_date': updated_date})
                                        if record.automatic_calculation_type == 'quarterly':
                                            if periodic_date == date.today():
                                                self.automatic_invoice_schedule_action(partner, record,partner_term)
                                                updated_date = periodic_date + relativedelta(months=3)
                                                partner_term.write({'execution_date': updated_date})
                                        if record.automatic_calculation_type == 'half_yearly':
                                            if periodic_date == date.today():
                                                self.automatic_invoice_schedule_action(partner, record, partner_term)
                                                updated_date = periodic_date + relativedelta(months=6)
                                                partner_term.write({'execution_date': updated_date})
                                        if record.automatic_calculation_type == 'annually':
                                            if periodic_date == date.today():
                                                self.automatic_invoice_schedule_action(partner, record,partner_term)
                                                updated_date = periodic_date + relativedelta(years=1)
                                                partner_term.write({'execution_date': updated_date})

    @api.multi
    def automatic_invoice_schedule_action(self, partner, record,partner_term):
        credit_value = partner_term.terms_id._get_term_value(partner=partner, invoice=False)
        if record.create_type == 'credit_note':
            if credit_value:
                credit_invoice = self.env['account.invoice'].create(
                    {'partner_id': partner.id,
                     'type': 'out_refund',
                     'journal_id': record.partner_term_journal_id.id}
                )
                if not record.partner_term_product_id.property_account_income_id:
                    raise ValidationError('No Account is defined for '
                                          'the Product associated with partner term')
                self.env['account.invoice.line'].create(
                    {'product_id': record.partner_term_product_id.id,
                     'name': record.name,
                     'account_id': record.partner_term_product_id.property_account_income_id.id,
                     'invoice_line_tax_ids': [(6, 0, record.partner_term_product_id.taxes_id.ids)],
                     'price_unit': credit_value,
                     'invoice_id': credit_invoice.id}
                )
                return credit_invoice._onchange_invoice_line_ids()
        if record.create_type == 'journal':
            if credit_value:
                credit_invoice = self.env['account.invoice'].create(
                    {'partner_id': partner.id,
                     'type': 'out_refund',
                     'journal_id': record.partner_term_journal_id.id}
                )
                if not partner_term.partner_term_product_id.property_account_income_id:
                    raise ValidationError('No Account is defined for '
                                          'the Product associated with partner term')
                self.env['account.invoice.line'].create(
                    {'product_id': record.partner_term_product_id.id,
                     'name': record.name,
                     'account_id': record.partner_term_product_id.property_account_income_id.id,
                     'invoice_line_tax_ids': [(6, 0, record.partner_term_product_id.taxes_id.ids)],
                     'price_unit': credit_value,
                     'invoice_id': credit_invoice.id}
                )
                return credit_invoice._onchange_invoice_line_ids()
        if record.create_type == 'vendor_bill':
            if credit_value:
                credit_invoice = self.env['account.invoice'].create(
                    {'partner_id': partner.id,
                     'type': 'in_invoice',
                     'journal_id': record.partner_term_journal_id.id}
                )
                if not record.partner_term_product_id.property_account_income_id:
                    raise ValidationError('No Account is defined for '
                                          'the Product associated with partner term')
                self.env['account.invoice.line'].create(
                    {'product_id': record.partner_term_product_id.id,
                     'name': record.name,
                     'account_id': record.partner_term_product_id.property_account_income_id.id,
                     'invoice_line_tax_ids': [(6, 0, record.partner_term_product_id.taxes_id.ids)],
                     'price_unit': credit_value,
                     'invoice_id': credit_invoice.id}
                )
                return credit_invoice._onchange_invoice_line_ids()
 # @api.multi
 #    def automatic_function_periodic_dialy(self):
 #        partners = self.env['res.partner'].search([('customer', '=', True)])
 #        for partner in partners:
 #            if partner.partner_terms_ids:
 #                for partner_term in partner.partner_terms_ids:
 #                    if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
 #                        if partner_term.frequency == 'periodic':
 #                            if partner_term.automatic_calculation_type == 'daily':
 #                                self.automatic_invoice_schedule_action(partner, partner_term)
 #
 #    @api.multi
 #    def automatic_function_periodic_weekly(self):
 #        partners = self.env['res.partner'].search([('customer', '=', True)])
 #        for partner in partners:
 #            if partner.partner_terms_ids:
 #                for partner_term in partner.partner_terms_ids:
 #                    if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
 #                        if partner_term.frequency == 'periodic':
 #                            if partner_term.automatic_calculation_type == 'weekly':
 #                                self.automatic_invoice_schedule_action(partner, partner_term)
 #
 #    @api.multi
 #    def automatic_function_periodic_monthly(self):
 #        partners = self.env['res.partner'].search([('customer', '=', True)])
 #        for partner in partners:
 #            if partner.partner_terms_ids:
 #                for partner_term in partner.partner_terms_ids:
 #                    if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
 #                        if partner_term.frequency == 'periodic':
 #                            if partner_term.automatic_calculation_type == 'monthly':
 #                                self.automatic_invoice_schedule_action(partner, partner_term)
 #
 #    @api.multi
 #    def automatic_function_periodic_quarterly(self):
 #        partners = self.env['res.partner'].search([('customer', '=', True)])
 #        for partner in partners:
 #            if partner.partner_terms_ids:
 #                for partner_term in partner.partner_terms_ids:
 #                    if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
 #                        if partner_term.frequency == 'periodic':
 #                            if partner_term.automatic_calculation_type == 'quarterly':
 #                                self.automatic_invoice_schedule_action(partner, partner_term)
 #
 #    @api.multi
 #    def automatic_function_periodic_half_yearly(self):
 #        partners = self.env['res.partner'].search([('customer', '=', True)])
 #        for partner in partners:
 #            if partner.partner_terms_ids:
 #                for partner_term in partner.partner_terms_ids:
 #                    if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
 #                        if partner_term.frequency == 'periodic':
 #                            if partner_term.automatic_calculation_type == 'half_yearly':
 #                                self.automatic_invoice_schedule_action(partner, partner_term)
 #
 #    @api.multi
 #    def automatic_function_periodic_annually(self):
 #        partners = self.env['res.partner'].search([('customer', '=', True)])
 #        for partner in partners:
 #            if partner.partner_terms_ids:
 #                for partner_term in partner.partner_terms_ids:
 #                    if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
 #                        if partner_term.frequency == 'periodic':
 #                            if partner_term.automatic_calculation_type == 'annually':
 #                                self.automatic_invoice_schedule_action(partner, partner_term)
# @api.multi
#     def automatic_function_only_once(self):
#         partners = self.env['res.partner'].search([('customer', '=', True)])
#         for partner in partners:
#             print(partner,'jghf')
#             if partner.partner_terms_ids :
#                 for partner_term in partner.partner_terms_ids:
#                     if partner_term and partner_term.active and partner_term.term_calculation_type == 'automatic':
#                         print(partner.name, '1')
#                         if partner_term.frequency == 'only_once' and partner.automatic_only_once:
#                             only_once_date = datetime.strptime(str(partner.automatic_only_once), '%Y-%m-%d').date()
#                             if only_once_date == date.today():
#                                 print(partner.name, '2')
#                                 self.automatic_invoice_schedule_action(partner, partner_term)
# if partner_term.automatic_calculation_type == 'daily':
#     self.automatic_invoice_schedule_action(partner, partner_term)
# if partner_term.automatic_calculation_type == 'weekly':
#     self.automatic_invoice_schedule_action(partner, partner_term)
# if partner_term.automatic_calculation_type == 'monthly':
#     self.automatic_invoice_schedule_action(partner, partner_term)
# if partner_term.automatic_calculation_type == 'quarterly':
#     self.automatic_invoice_schedule_action(partner, partner_term)
# if partner_term.automatic_calculation_type == 'half_yearly':
#     self.automatic_invoice_schedule_action(partner, partner_term)
# if partner_term.automatic_calculation_type == 'annually':
#     self.automatic_invoice_schedule_action(partner, partner_term)