# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from itertools import groupby
import operator
import pandas as pd
from datetime import datetime


class PendingSaleOrderWiz(models.TransientModel):
    _name = "od.pending.sale.order.wiz"
    _description = 'Pending Sale Orders' 

    date = fields.Datetime('Date As On',required=True)
    html_body = fields.Html(string="Body")
    html_from = fields.Html(string="From")
    html_to = fields.Html(string="To")
    html_cc = fields.Html(string="CC")
   
    def od_wiz_send_mail(self,template,data,summary,common_data,summary_sum,total_amount):
        ir_model_data = self.env['ir.model.data']
        mail_obj = self.env['mail.template']
        template_id = ir_model_data.get_object_reference('odx_despatch_v12', template)[1]
        template = mail_obj.browse(template_id)
        user = self.env.user
        context = self.env.context
        ctx  = context.copy()
        ctx['data'] =data 
        ctx['summary'] =summary 
        ctx['common_data'] = common_data
        ctx['summary_sum'] = summary_sum
        ctx['total_amount'] = total_amount
        from pprint import pprint
        pprint(ctx)
        template.with_context(ctx).send_mail(user.id,force_send=True)
        return True
#     
#     def get_trade(self,s):
#         return s[s.find("(")+1:s.find(")")]
#
    def get_seq(self,area):
        partner_area_obj = self.env['orchid.partner.area']
        seq = partner_area_obj.search([('name','=',area)]) and partner_area_obj.search([('name','=',area)]).seq or 100
        return seq
    
    @api.multi
    def send_report(self):
        date = self.date
        sale = self.env['sale.order']
        sale_orders = sale.search([('date_order','<=',date),('state','!=','cancel')])
        sale_ids = [sale.id for sale in sale_orders if sale.od_dms in ('draft','sale')]
        company_currency = self.env.user.company_id.currency_id
        state_dict = {'sale':'Sales Order','draft':'Quotation','deliverd':'Yet To Invoice','invoiced':'Invoiced'}

        data = [{'Order_No':sale.name,'Date':sale.date_order[:10],
                 'Party':sale.partner_id.name,
                 'Area':sale.partner_id and sale.partner_id.od_area_id and sale.partner_id.od_area_id.name or '',
                 'Amount':sale.pricelist_id.currency_id.compute(sale.amount_total,company_currency),
                 'State':state_dict[sale.od_dms],'Remarks':sale.note or '','Salesman':sale.user_id.name} for sale in sale.browse(sale_ids) if sale.od_dms in ('draft','sale')]
        
        total_amount = sum([sale.pricelist_id.currency_id.compute(sale.amount_total,company_currency) for sale in sale.browse(sale_ids) if sale.od_dms in ('draft','sale') ])
        total_amount = "{0:,.2f}".format(total_amount)
        df = pd.DataFrame(data)
        result = df.groupby(['Area','State']).sum()
        row_data = []
        for index, row in result.iterrows():
            row_data.append({'Amount':row.Amount.item(),
                            'Area':row.name[0],'State':row.name[1],
                          
                            
                            })
        summary = []
        for area,value in groupby(row_data,key=lambda x:x['Area']):
            qtn = devd = sale = inv = 0.0
            for val in list(value):
                if val.get('State') == 'Quotation':
                    qtn += val.get('Amount')
                if val.get('State') == 'Sales Order':
                    sale += val.get('Amount')
                    
            summary.append({'Area':area,'seq':self.get_seq(area),'qtn':"{0:,.2f}".format(qtn),'sale':"{0:,.2f}".format(sale),'total':"{0:,.2f}".format(sale+qtn),
                           })
        qtn =  sale  = 0.0
         
        for val in summary:
            qtn += float(val.get('qtn',0.0).replace(",",""))
            sale += float(val.get('sale',0.0).replace(",",""))
        summary_sum = {'qtn':"{0:,.2f}".format(qtn),'sale':"{0:,.2f}".format(sale),'total':"{0:,.2f}".format(sale+qtn)}
        for val in data:
            val['Amount'] = "{0:,.2f}".format(val['Amount'])
        summary =sorted(summary, key=lambda k: k['seq']) 
        data  = sorted(data, key=lambda k: k['Salesman']) 
        common_data = {'date':datetime.strptime(date,'%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")}
        self.od_wiz_send_mail('email_pending_sale_order_status_summary', data, summary,common_data,summary_sum,total_amount)
    
    
    @api.multi
    def show_template(self):
        date = self.date
        sale = self.env['sale.order']
        sale_orders = sale.search([('date_order','<=',date),('state','!=','cancel')])
        sale_ids = [sale.id for sale in sale_orders if sale.od_dms in ('draft','sale')]
        company_currency = self.env.user.company_id.currency_id
        state_dict = {'sale':'Sales Order','draft':'Quotation','deliverd':'Yet To Invoice','invoiced':'Invoiced'}

        data = [{'Order_No':sale.name,'Date':datetime.strptime(sale.date_order[:10],'%Y-%m-%d').strftime("%d-%m-%Y"),
                 'Party':sale.partner_id.name,
                 'Area':sale.partner_id and sale.partner_id.od_area_id and sale.partner_id.od_area_id.name or '',
                 'Amount':sale.pricelist_id.currency_id.compute(sale.amount_total,company_currency),
                 'State':state_dict[sale.od_dms],'Remarks':sale.note or '','Salesman':sale.user_id.name} for sale in sale.browse(sale_ids) if sale.od_dms in ('draft','sale')]
        
        total_amount = sum([sale.pricelist_id.currency_id.compute(sale.amount_total,company_currency) for sale in sale.browse(sale_ids) if sale.od_dms in ('draft','sale') ])
        total_amount = "{0:,.2f}".format(total_amount)
        df = pd.DataFrame(data)
        result = df.groupby(['Area','State']).sum()
        row_data = []
        for index, row in result.iterrows():
            row_data.append({'Amount':row.Amount.item(),
                            'Area':row.name[0],'State':row.name[1],
                          
                            
                            })
        summary = []
        for area,value in groupby(row_data,key=lambda x:x['Area']):
            qtn = devd = sale = inv = 0.0
            for val in list(value):
                if val.get('State') == 'Quotation':
                    qtn += val.get('Amount')
                if val.get('State') == 'Sales Order':
                    sale += val.get('Amount')
                    
            summary.append({'Area':area,'seq':self.get_seq(area),'qtn':"{0:,.2f}".format(qtn),'sale':"{0:,.2f}".format(sale),'total':"{0:,.2f}".format(sale+qtn),
                           })
        qtn =  sale  = 0.0
         
        for val in summary:
            qtn += float(val.get('qtn',0.0).replace(",",""))
            sale += float(val.get('sale',0.0).replace(",",""))
        summary_sum = {'qtn':"{0:,.2f}".format(qtn),'sale':"{0:,.2f}".format(sale),'total':"{0:,.2f}".format(sale+qtn)}
        for val in data:
            val['Amount'] = "{0:,.2f}".format(val['Amount'])
        summary =sorted(summary, key=lambda k: k['seq']) 
        data  = sorted(data, key=lambda k: k['Salesman']) 
        common_data = {'date':datetime.strptime(date,'%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")}
        # self.od_wiz_send_mail('email_pending_sale_order_status_summary', data, summary,common_data,summary_sum,total_amount)
        ir_model_data = self.env['ir.model.data']
        mail_obj = self.env['mail.template']
        template_id = ir_model_data.get_object_reference('odx_despatch_v12', 'email_pending_sale_order_status_summary')[1]
        template = mail_obj.browse(template_id)
        user = self.env.user
        context = self.env.context
        ctx  = context.copy()
        ctx['data'] =data 
        ctx['summary'] =summary 
        ctx['common_data'] = common_data
        ctx['summary_sum'] = summary_sum
        ctx['total_amount'] = total_amount
        generated_field_values = template.with_context(ctx).render_template(
            getattr(template, 'body_html'), template.model, [user.id],True)
        self.html_from = user.email
        self.html_to = template.email_to
        self.html_cc = template.email_cc
        self.html_body = generated_field_values[user.id]
        return {
            'name':'Pending Sales Orders',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'od.pending.sale.order.wiz',
            'res_id': self.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        } 