# -*- coding: utf-8 -*-

import logging
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class HrDocumentType(models.Model):
    _name = 'hr.document.type'
    _description = 'HR Document Type'
    
    name = fields.Char(string='Document Type', required=True, copy=False)
    type = fields.Selection([('emirate', 'Emirate'), 
                             ('passport', 'Passport'), 
                             ('visa', 'Visa'),
                             ('health', 'Health'), 
                             ('fire_safety','Fire & Safety'), 
                             ('hazmat','Hazmat'), 
                             ('other','Other')],
                            string='Type', required=True, copy=False, default='other')
    #code = fields.Char('Code', required=True)
    #company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
    
    #_sql_constraints = [
    #    ('code_company_uniq', 'unique (code, company_id)', 'The code of the document must be unique per company!'),
    #]
    

class HrEmployeeDocument(models.Model):
    _inherit = "hr.employee.document"

    @api.model
    def _default_type(self):
        return self.env['hr.document.type'].search([('type', '=', 'other')], limit=1)    
    
    type = fields.Many2one('hr.document.type', copy=False, required=True, default=_default_type)
    

    @api.multi
    def mail_reminder(self):
        expiry_notify_obj = self.env['hr.expiry.notification']        
        mail_temp_obj = self.env['mail.template']
        today = fields.Date.today()
        today = fields.Date.from_string(today)
        today_aftr_90 = today + timedelta(days=90)
        today_aftr_90_str = fields.Date.to_string(today_aftr_90)
        exps = self.search([('expiry_date', '<', today_aftr_90_str)])
        
        exp_ids = exps.mapped('id')
        exp_nots = expiry_notify_obj.search([('employee_document_id', 'in', exp_ids)])
        exps_not_ids = exp_nots.mapped('employee_document_id').mapped('id') 
        c_exps = exps.filtered(lambda r: r.id not in exps_not_ids) 
        #c_exps = exps.filtered(lambda r: exp_nots.employee_id and r.id != exp_nots.employee_id.id)
        w_exp_nots = self.env['hr.expiry.notification']
        for exp in exps:
            w_exp_nots += exp_nots.filtered(lambda r: r.employee_document_id and r.employee_document_id.id == exp.id)
        e_exp_nots = w_exp_nots.filtered(lambda r: r.days_left == 30)        
        
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])        
        format_date = lang and lang.date_format or '%B-%d-%Y'
        format_time = lang and lang.time_format or '%I-%M %p'
        template_90 = self.env.ref('cw_expiry_notifications.mail_template_emp_doc_exp_90')
        template_30 = self.env.ref('cw_expiry_notifications.mail_template_emp_doc_exp_30')
        assert template_90._name == 'mail.template' 
        assert template_30._name == 'mail.template'
        for exp in c_exps:  
            expire_date = exp.expiry_date
            expire_date = datetime.strptime(expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)
            exp_not = expiry_notify_obj.create({
                'name': _('Document-%s Expired On %s') % (exp.name, expire_date),
                'note': _('Document-%s Expired On %s') % (exp.name, expire_date),
                'type': exp.type and exp.type.type or 'other',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': exp.expiry_date,
                'employee_id': exp.employee_ref.id,
                'employee_document_id': exp.id,
                'other_id': exp.name,
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        for exp_not in e_exp_nots:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        return True

