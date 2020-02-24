# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from itertools import groupby
import operator
import pandas as pd
from datetime import datetime,timedelta


class DespatchReportWiz(models.TransientModel):
    _name = "od.despatch.report.wiz"
    _description = 'Despatch Report Wiz' 
    date_from = fields.Date('Date From',required=True)
    date_to = fields.Date('Date To',required=True,default=fields.Date.context_today)
    
    def od_wiz_send_mail(self,template,data,ctx_mail):
        ir_model_data = self.env['ir.model.data']
        mail_obj = self.env['mail.template']
        template_id = ir_model_data.get_object_reference('odx_despatch_v12', template)[1]
        
        template = mail_obj.browse(template_id)
        user = self.env.user
        context = self.env.context
        ctx  = context.copy()
        ctx['data'] = data 
        ctx.update(ctx_mail)
        
        
        template.with_context(ctx).send_mail(user.id,force_send=True)
        return True
    
    
    def days_between(self,d1, d2):
        from datetime import datetime
        d1 = datetime.strptime(str(d1), "%Y-%m-%d")
        d2 = datetime.strptime(str(d2), "%Y-%m-%d")
        return abs((d2 - d1).days)+1

   
        
    
    
    @api.multi
    def send_report(self):
        date_from,date_to = self.date_from,self.date_to
        no_of_days = self.days_between(date_from, date_to)
        company_currency = self.env.user.company_id.currency_id
        
        invoice = self.env['account.invoice']
        invoice_ids = invoice.search([('od_despatch_date','>=',date_from),('od_despatch_date','<=',date_to),('od_despatch_state','=','despatched')])
        inv_data =[{'despatch_date':datetime.strptime(inv.od_despatch_date,'%Y-%m-%d').strftime("%d-%m-%Y"),'bill':inv.number,'partner':inv.partner_id.name,
                    'carton':inv.no_of_carton,'link': 'http://172.16.0.35:5050/web#id=%s&view_type=form&model=account.invoice&action=196'%inv.id,
                'user':inv.user_id.name,'ref':inv.name,'desc':inv.od_desc,'user_id':inv.user_id.id,'div_mgr_email':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.div_mgr_id.login or ''} for inv in invoice_ids]
        
        user_data = {}
        for user,value in groupby(inv_data,key=lambda x:x['user_id']):
            list_val = user_data.get(user,[])
            list_val += value
            user_data[user] = list_val
            
        for user,value in user_data:
            ctx_mail = {}
            ctx_mail['email_to'] = self.env['res.users'].browse(user).login
            ctx_mail['email_cc'] = value[0].get('div_mgr_email','')
            ctx_mail['date_from'] = date_from
            ctx_mail['date_to'] = date_to
            self.od_wiz_send_mail('email_bfly_despatch_report', value,ctx_mail)
            
#         self.od_wiz_send_mail('email_bfly_daily_report', data)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
#             
#             summary.append({'Area':area,'Quotation':quotation,'SaleOrder':sale_order,'Delivered':deliverd,'Invoiced':invoiced})
#         self.od_wiz_send_mail('email_order_status_summary', data, summary)
    
    