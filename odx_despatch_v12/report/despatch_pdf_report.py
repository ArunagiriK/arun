# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import api, fields, models


class ReportDespatchPdf(models.AbstractModel):
    _name = 'report.odx_despatch_v12.report_despatch'

    def get_despatch_bycustomer(self,customer,docids):
        data = {}
        invoiceId = ""
        cartonNo = ""
        iDesc = ""
        total_cartons = 0
        invoices = self.env['account.invoice'].search([('partner_id','=',customer),('id','in',docids)])
        for invoice in invoices:
            
            if invoice.number:
                if invoiceId != "":
                    invoiceId = invoiceId + " ,"
                invoiceId = invoiceId + str(invoice.number)
            if cartonNo !="":
                cartonNo = cartonNo + " ,"
            cartonNo = cartonNo + str(invoice.no_of_carton)

            total_cartons = total_cartons + int(invoice.no_of_carton)
            if invoice.od_desc:
                iDesc = iDesc + str(invoice.od_desc) + " ,"

        data.update({
            'invoiceId':invoiceId,
            'pname':invoice[0].partner_id.name,
            'pstreet':invoice[0].partner_id.street,
            'pcity':invoice[0].partner_id.city,
            'description':iDesc,
            'carton_no':cartonNo,
            'noof_cartons':total_cartons,
            })
        return data

    @api.model
    def render_html(self, docids, data=None):
        lines_to_display = []
        customers = []
        for docid in docids:
            customer = self.env['account.invoice'].browse(docid).partner_id.id
            if customer not in customers:
                customers.append(customer)
        for cust in customers:
            line = self.get_despatch_bycustomer(cust,docids)
            lines_to_display.append(line)
        info  = self.env['account.invoice'].browse(docids[0])
        delvery_info = {
        'date':datetime.strptime(info.od_despatch_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        'driver':info.od_driver_id.name,
        'veh_no':info.od_fleet_id.name
        }
        docargs = {
            'doc_ids': docids,
            # 'doc_model': 'res.partner',
            # 'docs': self.env['res.partner'].browse(docids),
            # 'time': time,
            'Lines': lines_to_display,
            'info':delvery_info,
            # 'Totals': totals,
            # 'Date': fields.date.today(),
        }
        return self.env['report'].render('odx_despatch_v12.report_despatch', values=docargs)




class ReportExportInvoicePdf(models.AbstractModel):
    _name = 'report.odx_despatch_v12.report_export_invoice'

    def get_invoice_bycustomer(self,customer,docids):
        data = {}
        line = []
        invoice_numbers = ""
        lpo_nos = ""
        no_of_cartons = 0
        invoices = self.env['account.invoice'].search([('partner_id','=',customer),('id','in',docids)])
        for invoice in invoices:
            if invoice_numbers != "":
                invoice_numbers = invoice_numbers + ", "
            invoice_numbers = invoice_numbers + str(invoice.number)
            if lpo_nos != "":
                lpo_nos = lpo_nos + ", "
            lpo_nos = lpo_nos + str(invoice.name)
            no_of_cartons = no_of_cartons + invoice.no_of_carton
            for invoice_line_id in invoice.invoice_line_ids:
                line.append({
                    'article':str(invoice_line_id.od_article_no or ''),
                    'carton':invoice_line_id.od_carton_no,
                    'country':invoice_line_id.product_id and invoice_line_id.product_id.orchid_country_id and invoice_line_id.product_id.orchid_country_id.name or '',
                    'description':invoice_line_id.product_id.name,
                    'quantity':invoice_line_id.quantity,
                    'rate':invoice_line_id.price_unit,
                    'amount':invoice_line_id.price_subtotal,                    
                    })
        data.update({
            'partner':str(invoices[0].partner_id.name)+ " " +str(invoices[0].partner_id.street)+ " " +str(invoices[0].partner_id.country_id.name),
            'tel':invoices[0].partner_id and invoices[0].partner_id.phone or None,
            'fax':invoices[0].partner_id and invoices[0].partner_id.fax or None,
            'del_loc':invoices[0].od_deliveryloc_id and invoices[0].od_deliveryloc_id.name or None,
            'inv_no':invoice_numbers,
            'date':invoices[0].date_invoice and datetime.strptime(invoices[0].date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y") or None,
            'lpo_no':lpo_nos,
            'sales_man':invoices[0].user_id.name,
            'total_crtns':no_of_cartons,
            'invoice_line':line,
            'currency_id' :invoices[0].currency_id and invoices[0].currency_id.name or None,
            }) 
        return data

    @api.model
    def render_html(self, docids, data=None):
        lines_to_display = []
        customers = []
        
        
        sales_man = ""
        for docid in docids:
            invoice = self.env['account.invoice'].browse(docid)
            customer = invoice.partner_id.id
            
            
            if customer not in customers:
                customers.append(customer)
        for cust in customers:
            line = self.get_invoice_bycustomer(cust,docids)
            lines_to_display.append(line)
        info  = self.env['account.invoice'].browse(docids[0])
        
        docargs = {
            'doc_ids': docids,
            'customers': lines_to_display,
        }
        return self.env['report'].render('odx_despatch_v12.report_export_invoice', values=docargs)
