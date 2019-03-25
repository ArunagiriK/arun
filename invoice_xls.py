# -*- coding: utf-8 -*-

import xlwt
import base64
import calendar
from io import StringIO
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import date
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class InvoiceReport(models.TransientModel):
    _name = "invoice.report"
    
    start_date = fields.Date(string='Start Date', required=True, default=date.today() - relativedelta(months=+6))
    end_date = fields.Date(string="End Date", required=True, default=fields.Date.context_today)
    code_partner = fields.Char('Préfixe des codes partenaire')
    invoice_state = fields.Selection([
            ('open', 'Open'),
            ('paid', 'Paid'),
        ], string='Status', default='open', required=True)
    invoice_data = fields.Char('Name',)
    file_name = fields.Binary('Invoice Excel Report', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')


    @api.multi
    def action_invoice_report(self):
        record = self.env['account.invoice'].search([('date_invoice', '>=', self.start_date), ('date_invoice', '<=', self.end_date),('partner_id.ref','=',self.code_partner)])
        if record:
            file = StringIO()
            final_value = {}
            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet('Invoices',cell_overwrite_ok=True)
            sheet.col(0).width = int(30*260)
            sheet.col(1).width = int(30*260)
            sheet.col(2).width = int(18*260)
            sheet.col(3).width = int(18*260)
            sheet.col(4).width = int(33*260)
            sheet.col(5).width = int(15*260)
            sheet.col(6).width = int(18*260)
            format0 = xlwt.easyxf('font:height 500,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center')
            format1 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            format2 = xlwt.easyxf('font:bold True;align: horiz left')
            format3 = xlwt.easyxf('align: horiz left')
            format4 = xlwt.easyxf('align: horiz right')
            format5 = xlwt.easyxf('font:bold True;align: horiz right')
            format6 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz right')
            format7 = xlwt.easyxf('font:bold True;borders:top thick;align: horiz right')
            format8 = xlwt.easyxf('font:bold True;borders:top thick;pattern: pattern solid, fore_colour gray25;align: horiz left')

            sheet.write(0, 0, 'Titre', format1)
            sheet.write(0, 1, 'Gencod', format1)
            sheet.write(0, 2, 'Date de facture', format1)
            sheet.write(0, 3, 'Total HT', format1)
            sheet.write(0, 4, 'Total TTC', format1)
            sheet.write(0, 5, 'Numéro de facture', format1)
            sheet.write(0, 6, 'Quantité', format6)
            sheet.write(0, 7, 'PPHT', format6)
            sheet.write(0, 8, 'PPTTC', format1)
            sheet.write(0, 9, 'SUBTOTAL', format6)
            row = 1
            for rec in record:
                invoice_lines = []
                for lines in rec.invoice_line_ids:
                    product = {
                        'product_id'     : lines.product_id.name if lines.product_id else '',
                        'description'    : lines.name,
                        'product_id.barcode'    : lines.product_id.barcode  if lines.product_id else '',
                        'quantity'       : lines.quantity,
                        'price_unit'     : lines.price_unit,
                        'price_subtotal' : lines.price_subtotal
                    }
                    if lines.invoice_line_tax_ids:
                        taxes = []
                        for tax_id in lines.invoice_line_tax_ids:
                            taxes.append(tax_id.name)
                        product['invoice_line_tax_ids'] = taxes
                    invoice_lines.append(product)
                final_value['partner_id'] = rec.partner_id.name
                final_value['date_invoice'] = rec.date_invoice
                final_value['date_due'] = rec.date_due
                final_value['number'] = rec.number
                final_value['currency_id'] = rec.currency_id
                final_value['state'] = dict(self.env['account.invoice'].fields_get(allfields=['state'])['state']['selection'])[rec.state]
                final_value['payment_term_id'] = rec.payment_term_id.name
                final_value['origin'] = rec.origin
                final_value['amount_untaxed'] = rec.amount_untaxed
                final_value['amount_tax'] = rec.amount_tax
                final_value['amount_total'] = rec.amount_total
                final_value['residual'] = rec.residual
                final_value['payments_widget'] = rec.payments_widget
                final_value['outstanding_credits_debits_widget'] = rec.outstanding_credits_debits_widget
                # ~ invoice_number = rec.number.split('/')
                for inv_line in invoice_lines:
                    sheet.write(row, 0, inv_line.get('product_id'), format3)
                    sheet.write(row, 1, inv_line.get('product_id.barcode'), format3)
                    sheet.write(row, 2, str(final_value['date_invoice']), format3)
                    sheet.write(row, 3, final_value['amount_untaxed'], format3)
                    sheet.write(row, 4, final_value['amount_total'], format3)
                    sheet.write(row, 5, final_value['number'], format3)
                    sheet.write(row, 6, inv_line.get('quantity'), format4)
                    sheet.write(row, 7, inv_line.get('price_unit'), format4)
                    print (row)
                    sheet.write(row, 8, inv_line.get('price_unit'), format4)
                    if final_value['currency_id'].position == "before":
                        sheet.write(row, 9, str(final_value['currency_id'].symbol) + str(inv_line.get('price_subtotal')), format4)
                    else:
                        sheet.write(row, 9, str(inv_line.get('price_subtotal')) + str(final_value['currency_id'].symbol), format4)
                    row += 1
                #~ sheet.write(row, 5, 'Total HT', format8)
                #~ sheet.write(row+2, 5, 'Total TTC ', format8)
                #~ sheet.write(row+4, 5, 'AMOUNT DUE', format8)
                #~ if final_value['currency_id'].position == "before":
                    #~ sheet.write(row, 6, str(final_value['currency_id'].symbol) + str(final_value['amount_untaxed']), format7)
                    #~ sheet.write(row+2, 6, str(final_value['currency_id'].symbol) + str(final_value['amount_total']), format7)
                #~ else:
                    #~ sheet.write(row, 6, str(final_value['amount_untaxed']) + str(final_value['currency_id'].symbol), format7)
                    #~ sheet.write(row+2, 6, str(final_value['amount_total']) + str(final_value['currency_id'].symbol), format7)
                    #~ sheet.write(row+4, 6, str(final_value['residual']) + str(final_value['currency_id'].symbol), format7)
        else:
            raise Warning("Currently No Invoice/Bills For This Data!!")
        filename = ('Invoice Report'+ '.xls')
        workbook.save(filename)
        file = open(filename, "rb")
        file_data = file.read()
        out = base64.encodestring(file_data)
        self.write({'state': 'get', 'file_name': out, 'invoice_data':'Invoice Report.xls'})
        return {
           'type': 'ir.actions.act_window',
           'res_model': 'invoice.report',
           'view_mode': 'form',
           'view_type': 'form',
           'res_id': self.id,
           'target': 'new',
        }
