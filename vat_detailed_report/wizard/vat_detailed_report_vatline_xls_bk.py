# -*- encoding: utf-8 -*-

import base64
import io
from io import StringIO
from io import BytesIO
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat
from odoo import models, fields, api
import xlsxwriter

class AccountVatDetailedReportWizard(models.TransientModel):
    _inherit = "account.vat.detailed.report.wizard"   

    excel_file = fields.Binary(string='Excel Report',readonly="1")
    file_name = fields.Char(string='Excel File',readonly="1")
    

    @api.multi
    def export_account_vat_detailed_report(self):
        self.ensure_one()
        if self.product_details:
            return self.generate_product_excel()  
        else:
            return self.generate_tax_excel()    

    def write_tax_lines(self, sheet, row, tax_detail_data, data_format, total_format):        
        lang_code = self.env.user.lang or 'en_US'
        timezone = self.env.user.partner_id.tz or 'UTC'
        timezone = pycompat.to_native(timezone) 
        self_tz = self.with_context(tz=timezone)        
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        time_format = lang_id.time_format        
        datetime_format = ' '.join([date_format, time_format])
        total_tax_base_amount = 0.0
        total_balance = 0.0
        for tax_detail_line in tax_detail_data:
            tax_base_amount = abs(tax_detail_line.get('tax_base_amount', 0.0))
            total_tax_base_amount += tax_base_amount
            balance = abs(tax_detail_line.get('balance', 0.0))
            total_balance += balance
            mv_date = ''
            if tax_detail_line.get('mv_date', False): 
                mv_date = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(tax_detail_line['mv_date'])).strftime(date_format)
            sheet.write(row, 0, tax_detail_line.get('mv_name'), data_format)     
            sheet.write(row, 1, tax_detail_line.get('mv_ref'), data_format)   
            sheet.write(row, 2, mv_date, data_format)   
            sheet.write(row, 3, tax_detail_line.get('inv_number'), data_format) 
            sheet.write(row, 4, tax_detail_line.get('partner_name'), data_format)         
            sheet.write(row, 5, tax_detail_line.get('tax_name'), data_format)   
            sheet.write(row, 6, tax_base_amount, data_format)   
            sheet.write(row, 7, balance, data_format)
            row += 1
        sheet.merge_range(row, 0, row, 5, 'Total : ', total_format)  
        sheet.write(row, 6, total_tax_base_amount, total_format) 
        sheet.write(row, 7, total_balance, total_format)
        row += 1        
        return row

    def get_tax_line_detail_data(self, move_types=[]):
        query_type = """  """
        args_list = ()
        if move_types:
            args_list += (tuple(move_types),)
            query_type = """ mv.move_type IN %s AND """
        args_list += (self.from_date, self.to_date, self.company_id.id)
        req = """
                SELECT DISTINCT(mv_line.id) AS mv_line_id, mv.id AS mv_id, 
                    mv_line.tax_base_amount, 
                    mv_line.debit, mv_line.credit, mv_line.balance,  
                    mv_line.name AS mv_line_name, 
                    mv.name AS mv_name, 
                    mv.ref AS mv_ref, 
                    mv.date AS mv_date, 
                    mv.move_type AS mv_type, 
                    partner.name AS partner_name, 
                    line_tax.name AS tax_name,
                    account.name AS account_name,
                    invoice.name AS inv_name, 
                    invoice.number AS inv_number, 
                    invoice.origin AS inv_origin, 
                    invoice.reference AS inv_reference
                    FROM account_move_line  AS mv_line 
                    INNER JOIN account_move AS mv 
                        ON mv.id = mv_line.move_id 
                    INNER JOIN account_account AS account 
                        ON account.id = mv_line.account_id 
                    INNER JOIN account_tax AS line_tax 
                        ON line_tax.id = mv_line.tax_line_id 
                    LEFT JOIN account_invoice AS invoice 
                        ON invoice.id = mv_line.invoice_id 
                    LEFT JOIN res_partner AS partner 
                        ON partner.id = mv_line.partner_id
                    WHERE 
                        mv_line.tax_exigible AND
                        """ + query_type + """
                        mv_line.date >= %s AND 
                        mv_line.date <= %s AND 
                        mv_line.company_id = %s
                    ORDER BY mv.date ASC
            """
        self.env.cr.execute(req, args_list)
        tax_detail_data = self.env.cr.dictfetchall()
        return tax_detail_data

    def generate_tax_excel(self):        
        #fp = StringIO()     
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp, {})
        company_id = self.company_id.id
        company = self.env['res.company'].browse(company_id)
        to_date = self.to_date
        to_date1 = str(to_date)
        tax_year = to_date1[0:4]
        from_date = self.from_date
        vat_detailed_period = "From: " + from_date + " To: " + to_date

        format1 = workbook.add_format({'font_size': 11, 'bg_color': '#E0FFFF', 'bold':True, 'font_name': 'Arial', 'border':True, 'align': 'center'})
        format2 = workbook.add_format({'font_size': 10, 'bg_color': '#E0FFFF', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'border': True, 'align': 'center'})
        format4 = workbook.add_format({'font_size': 10, 'bg_color': '#E0FFFF', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'left'})
        format5 = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'border': True, 'align': 'right'})
        format6 = workbook.add_format({'font_size': 10, 'bg_color': '#E0FFFF', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'right'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#A9A9A9', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'right'})
        format8 = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'border': True, 'align': 'left'})

        sheet = workbook.add_worksheet("VAT Detailed Report")
        sheet.set_column('A:A', 35)
        sheet.set_column('B:I', 15)
        sheet.merge_range('A3:G3', "VAT Detailed Report", format1)
        sheet.merge_range('A6:B6', 'Taxable Person Details', format2)

        sheet.write(6, 0, 'TRN', format2)
        sheet.write(6,1,company.vat, format3)

        sheet.write(7, 0, 'Taxable Person Name', format2)
        sheet.write(7, 1, company.name, format3)

        sheet.merge_range('A9:B9', 'Tax Year', format2)
        sheet.merge_range('A11:B11', tax_year, format3)

        sheet.merge_range('C9:D9', 'VAT Detailed Period', format2)
        sheet.merge_range('C11:D11', vat_detailed_period, format3)
        
        tax_receivable_data = self.get_tax_line_detail_data(move_types=['receivable'])
        tax_receivable_refund_data = self.get_tax_line_detail_data(move_types=['receivable_refund'])
        tax_payable_data = self.get_tax_line_detail_data(move_types=['payable'])
        tax_payable_refund_data = self.get_tax_line_detail_data(move_types=['payable_refund'])
        row = 12
        #sheet.write(row, 0, 'Journal Entry', format4)
        sheet.write(row, 0, 'Journal Entry', format6)
        sheet.write(row, 1, 'Ref', format6)
        sheet.write(row, 2, 'Date', format6)
        sheet.write(row, 3, 'Invoice Number', format6)
        sheet.write(row, 4, 'Partner', format6)
        sheet.write(row, 5, 'Tax Rate', format6)
        sheet.write(row, 6, 'Taxable Amount', format6)
        sheet.write(row, 7, 'Tax Amount', format6)        
        row += 1
        sheet.merge_range(row, 0, row, 7, 'Taxes Received', format2)
        row += 1
        row = self.write_tax_lines(sheet, row, tax_receivable_data, format5, format7)   
        sheet.merge_range(row, 0, row, 7, 'Taxes Paid On Credit Notes', format2)     
        row += 1
        row = self.write_tax_lines(sheet, row, tax_receivable_refund_data, format5, format7)  
        sheet.merge_range(row, 0, row, 7, 'Taxes Paid', format2)    
        row += 1
        row = self.write_tax_lines(sheet, row, tax_payable_data, format5, format7)       
        sheet.merge_range(row, 0, row, 7, 'Taxes Received On Debit Notes', format2)      
        row += 1
        row = self.write_tax_lines(sheet, row, tax_payable_refund_data, format5, format7)
            
                  
        workbook.close()
        #fp.seek(0)
        #print (fp.read(), 'xlsx')
        
        excel_file = base64.encodestring(fp.getvalue())
        self.excel_file = excel_file
        self.file_name = "Vat Detailed Report "+vat_detailed_period+".xlsx"
        fp.close()
        return {
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'account.vat.detailed.report.wizard',
              'res_id': self.id,
              'type': 'ir.actions.act_window',
              'target': 'new'
              }
        