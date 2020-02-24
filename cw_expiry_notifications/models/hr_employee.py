# -*- coding: utf-8 -*-

import logging
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    def action_schedule_emp_notification(self):
        expiry_notify_obj = self.env['hr.expiry.notification']        
        mail_temp_obj = self.env['mail.template']
        today = fields.Date.today()
        today = fields.Date.from_string(today)
        today_aftr_90 = today + timedelta(days=90)
        today_aftr_90_str = fields.Date.to_string(today_aftr_90)
        emp_emir_exps = self.search([('emirate_expire', '<', today_aftr_90_str)])
        emp_pass_exps = self.search([('passport_expire', '<', today_aftr_90_str)])
        emp_visa_exps = self.search([('visa_expire', '<', today_aftr_90_str)])
        emp_health_exps = self.search([('healthcard_expire', '<', today_aftr_90_str)])
        emp_fire_exps = self.search([('fire_safety_expire', '<', today_aftr_90_str)])
        emp_haz_exps = self.search([('hazmat_expire', '<', today_aftr_90_str)])
        
        emp_ids = emp_emir_exps.mapped('id')
        emir_exps = expiry_notify_obj.search([('type', '=', 'emirate'), ('employee_id', 'in', emp_ids)])
        exps_emp_ids = emir_exps.mapped('employee_id').mapped('id') 
        c_emp_emir_exps = emp_emir_exps.filtered(lambda r: r.id not in exps_emp_ids) 
        #c_emp_emir_exps = emp_emir_exps.filtered(lambda r: emir_exps.employee_id and r.id != emir_exps.employee_id.id)
        w_emir_exps = emir_exps.filtered(lambda r: r.employee_id and r.employee_id.id in emp_ids)
        e_emir_exps = w_emir_exps.filtered(lambda r: r.days_left == 30)        
        
        emp_ids = emp_pass_exps.mapped('id')
        pass_exps = expiry_notify_obj.search([('type', '=', 'passport'), ('employee_id', 'in', emp_ids)])
        exps_emp_ids = pass_exps.mapped('employee_id').mapped('id') 
        c_emp_pass_exps = emp_pass_exps.filtered(lambda r: r.id not in exps_emp_ids) 
        #c_emp_pass_exps = emp_pass_exps.filtered(lambda r: pass_exps.employee_id and r.id != pass_exps.employee_id.id)
        w_pass_exps = pass_exps.filtered(lambda r: r.employee_id and r.employee_id.id in emp_ids)
        e_pass_exps = w_pass_exps.filtered(lambda r: r.days_left == 30)
        
        emp_ids = emp_visa_exps.mapped('id')
        visa_exps = expiry_notify_obj.search([('type', '=', 'visa'), ('employee_id', 'in', emp_ids)])
        exps_emp_ids = visa_exps.mapped('employee_id').mapped('id') 
        c_emp_visa_exps = emp_visa_exps.filtered(lambda r: r.id not in exps_emp_ids) 
        #c_emp_visa_exps = emp_visa_exps.filtered(lambda r: visa_exps.employee_id and r.id != visa_exps.employee_id.id)
        w_visa_exps = visa_exps.filtered(lambda r: r.employee_id and r.employee_id.id in emp_ids)
        e_visa_exps = w_visa_exps.filtered(lambda r: r.days_left == 30)
        
        emp_ids = emp_health_exps.mapped('id')
        health_exps = expiry_notify_obj.search([('type', '=', 'health'), ('employee_id', 'in', emp_ids)])
        exps_emp_ids = health_exps.mapped('employee_id').mapped('id') 
        c_emp_health_exps = emp_health_exps.filtered(lambda r: r.id not in exps_emp_ids) 
        #c_emp_health_exps = emp_health_exps.filtered(lambda r: health_exps.employee_id and r.id != health_exps.employee_id.id)
        w_health_exps = health_exps.filtered(lambda r: r.employee_id and r.employee_id.id in emp_ids)
        e_health_exps = w_health_exps.filtered(lambda r: r.days_left == 30)
        
        emp_ids = emp_fire_exps.mapped('id')
        fire_exps = expiry_notify_obj.search([('type', '=', 'fire_safety'), ('employee_id', 'in', emp_ids)])
        exps_emp_ids = fire_exps.mapped('employee_id').mapped('id') 
        c_emp_fire_exps = emp_fire_exps.filtered(lambda r: r.id not in exps_emp_ids) 
        #c_emp_fire_exps = emp_fire_exps.filtered(lambda r: fire_exps.employee_id and r.id != fire_exps.employee_id.id)
        w_fire_exps = fire_exps.filtered(lambda r: r.employee_id and r.employee_id.id in emp_ids)
        e_fire_exps = w_fire_exps.filtered(lambda r: r.days_left == 30)
        
        emp_ids = emp_haz_exps.mapped('id')
        haz_exps = expiry_notify_obj.search([('type', '=', 'hazmat'), ('employee_id', 'in', emp_ids)])
        exps_emp_ids = haz_exps.mapped('employee_id').mapped('id') 
        c_emp_haz_exps = emp_haz_exps.filtered(lambda r: r.id not in exps_emp_ids) 
        #c_emp_haz_exps = emp_haz_exps.filtered(lambda r: haz_exps.employee_id and r.id != haz_exps.employee_id.id)
        w_haz_exps = haz_exps.filtered(lambda r: r.employee_id and r.employee_id.id in emp_ids)
        e_haz_exps = w_fire_exps.filtered(lambda r: r.days_left == 30)        
        
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])        
        format_date = lang and lang.date_format or '%B-%d-%Y'
        format_time = lang and lang.time_format or '%I-%M %p'
        template_90 = self.env.ref('cw_expiry_notifications.mail_template_emp_doc_exp_90')
        template_30 = self.env.ref('cw_expiry_notifications.mail_template_emp_doc_exp_30')
        assert template_90._name == 'mail.template' 
        assert template_30._name == 'mail.template'                       
            
        for emp in c_emp_emir_exps:  
            emp_expire_date = emp.emirate_expire
            expire_date = datetime.strptime(emp_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date) 
            print ("expire_date",expire_date)          
            exp_not = expiry_notify_obj.create({
                'name': 'Emirates ID Expiry of : ' + emp.name,
                'note': 'Emirates ID of employee ' + emp.name + ' will expire on ' + expire_date,
                'type': 'emirate',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_expire_date,
                'employee_id': emp.id,
                'type_of_document': 'Emirates ID'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for emp in c_emp_pass_exps:  
            emp_expire_date = emp.passport_expire
            expire_date = datetime.strptime(str(emp_expire_date), DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Passport Expiry of : ' + emp.name,
                'note': 'Passport of employee ' + emp.name + ' will expire on ' + expire_date,
                'type': 'passport',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_expire_date,
                'employee_id': emp.id,
                'type_of_document': 'Passport'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                
        for emp in c_emp_visa_exps:  
            emp_expire_date = emp.visa_expire
            expire_date = datetime.strptime(emp_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Visa Expiry of : ' + emp.name,
                'note': 'Visa of employee ' + emp.name + ' will expire on ' + expire_date,
                'type': 'visa',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_expire_date,
                'employee_id': emp.id,
                'type_of_document': 'Visa'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                
        for emp in c_emp_health_exps:  
            emp_expire_date = emp.healthcard_expire
            expire_date = datetime.strptime(emp_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Healthcard Expiry of : ' + emp.name,
                'note': 'Healthcard of employee ' + emp.name + ' will expire on ' + expire_date,
                'type': 'health',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_expire_date,
                'employee_id': emp.id,
                'type_of_document': 'Health Card'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                
        for emp in c_emp_fire_exps:  
            emp_expire_date = emp.fire_safety_expire
            expire_date = datetime.strptime(emp_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Fire and Safety Certificate Expiry of : ' + emp.name,
                'note': 'Fire and Safety Certificate of employee ' + emp.name + ' will expire on ' + expire_date,
                'type': 'fire_safety',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_expire_date,
                'employee_id': emp.id,
                'type_of_document': 'Fire and Safety Certificate'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for emp in c_emp_haz_exps:  
            emp_expire_date = emp.hazmat_expire
            expire_date = datetime.strptime(emp_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'HAZMAT Certificate Expiry of : ' + emp.name,
                'note': 'HAZMAT Certificate of employee ' + emp.name + ' will expire on ' + expire_date,
                'type': 'hazmat',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_expire_date,
                'employee_id': emp.id,
                'type_of_document': 'HAZMAT Certificate'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                     
        for exp_not in e_emir_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_pass_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_visa_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_health_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_fire_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_haz_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        return True
    
    
    
class HrDependentsLine(models.Model):    
    _inherit = "hr.dependents.line"

    @api.multi
    def action_schedule_emp_dep_notification(self):
        expiry_notify_obj = self.env['hr.expiry.notification']        
        mail_temp_obj = self.env['mail.template']
        today = fields.Date.today()
        today = fields.Date.from_string(today)
        today_aftr_90 = today + timedelta(days=90)
        today_aftr_90_str = fields.Date.to_string(today_aftr_90)
        emp_dep_emir_exps = self.search([('emirate_expire', '<', today_aftr_90_str)])
        emp_dep_pass_exps = self.search([('passport_expire', '<', today_aftr_90_str)])
        emp_dep_visa_exps = self.search([('visa_expire', '<', today_aftr_90_str)])
        emp_dep_health_exps = self.search([('healthcard_expire', '<', today_aftr_90_str)])
        
        #emp_dep_ids = emp_dep_emir_exps.mapped('employee_id').mapped('id')
        dep_ids = emp_dep_emir_exps.mapped('id')        
        emir_exps = expiry_notify_obj.search([('type', '=', 'emirate'), ('dependent_id', 'in', dep_ids)])
        exps_emp_dep_ids = emir_exps.mapped('dependent_id').mapped('id') 
        c_emp_dep_emir_exps = emp_dep_emir_exps.filtered(lambda r: r.id not in exps_emp_dep_ids) 
        #c_emp_dep_emir_exps = emp_dep_emir_exps.filtered(lambda r: emir_exps.employee_id and r.employee_id.id != emir_exps.employee_id.id)
        w_emir_exps = emir_exps.filtered(lambda r: r.dependent_id and r.dependent_id.id in dep_ids)
        e_emir_exps = w_emir_exps.filtered(lambda r: r.days_left == 30)        
        
        #emp_dep_ids = emp_dep_pass_exps.mapped('employee_id').mapped('id')
        dep_ids = emp_dep_pass_exps.mapped('id')        
        pass_exps = expiry_notify_obj.search([('type', '=', 'passport'), ('dependent_id', 'in', dep_ids)])
        exps_emp_dep_ids = pass_exps.mapped('dependent_id').mapped('id') 
        c_emp_dep_pass_exps = emp_dep_pass_exps.filtered(lambda r: r.id not in exps_emp_dep_ids) 
        #c_emp_dep_pass_exps = emp_dep_pass_exps.filtered(lambda r: pass_exps.employee_id and r.employee_id.id != pass_exps.employee_id.id)
        w_pass_exps = pass_exps.filtered(lambda r: r.dependent_id and r.dependent_id.id in dep_ids)
        e_pass_exps = w_pass_exps.filtered(lambda r: r.days_left == 30)
        
        #emp_dep_ids = emp_dep_visa_exps.mapped('employee_id').mapped('id')
        dep_ids = emp_dep_visa_exps.mapped('id')        
        visa_exps = expiry_notify_obj.search([('type', '=', 'visa'), ('dependent_id', 'in', dep_ids)])
        exps_emp_dep_ids = visa_exps.mapped('dependent_id').mapped('id') 
        c_emp_dep_visa_exps = emp_dep_visa_exps.filtered(lambda r: r.id not in exps_emp_dep_ids) 
        #c_emp_dep_visa_exps = emp_dep_visa_exps.filtered(lambda r: visa_exps.employee_id and r.employee_id.id != visa_exps.employee_id.id)
        w_visa_exps = visa_exps.filtered(lambda r: r.dependent_id and r.dependent_id.id in dep_ids)
        e_visa_exps = w_visa_exps.filtered(lambda r: r.days_left == 30)
        
        #emp_dep_ids = emp_dep_health_exps.mapped('employee_id').mapped('id')
        dep_ids = emp_dep_health_exps.mapped('id')        
        health_exps = expiry_notify_obj.search([('type', '=', 'health'), ('dependent_id', 'in', dep_ids)])
        exps_emp_dep_ids = health_exps.mapped('dependent_id').mapped('id') 
        c_emp_dep_health_exps = emp_dep_health_exps.filtered(lambda r: r.id not in exps_emp_dep_ids) 
        #c_emp_dep_health_exps = emp_dep_health_exps.filtered(lambda r: health_exps.employee_id and r.employee_id.id != health_exps.employee_id.id)
        w_health_exps = health_exps.filtered(lambda r: r.dependent_id and r.dependent_id.id in dep_ids)
        e_health_exps = w_health_exps.filtered(lambda r: r.days_left == 30)        
        
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])        
        format_date = lang and lang.date_format or '%B-%d-%Y'
        format_time = lang and lang.time_format or '%I-%M %p'
        template_90 = self.env.ref('cw_expiry_notifications.mail_template_emp_dep_doc_exp_90')
        template_30 = self.env.ref('cw_expiry_notifications.mail_template_emp_dep_doc_exp_30')
        assert template_90._name == 'mail.template' 
        assert template_30._name == 'mail.template'                       
            
        for emp_dep in c_emp_dep_emir_exps:  
            emp_dep_expire_date = emp_dep.emirate_expire
            expire_date = datetime.strptime(emp_dep_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date) 
            print ("expire_date",expire_date)          
            exp_not = expiry_notify_obj.create({
                'name': 'Emirates ID Expiry of : ' + emp_dep.name,
                'note': 'Emirates ID of employee ' + emp_dep.name + ' will expire on ' + expire_date,
                'type': 'emirate',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_dep_expire_date,
                'employee_id': emp_dep.employee_id.id,
                'type_of_document': 'Emirates ID'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for emp_dep in c_emp_dep_pass_exps:  
            emp_dep_expire_date = emp_dep.passport_expire
            expire_date = datetime.strptime(emp_dep_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Passport Expiry of : ' + emp_dep.name,
                'note': 'Passport of employee ' + emp_dep.name + ' will expire on ' + expire_date,
                'type': 'passport',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_dep_expire_date,
                'employee_id': emp_dep.employee_id.id,
                'type_of_document': 'Passport'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                
        for emp_dep in c_emp_dep_visa_exps:  
            emp_dep_expire_date = emp_dep.visa_expire
            expire_date = datetime.strptime(emp_dep_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Visa Expiry of : ' + emp_dep.name,
                'note': 'Visa of employee ' + emp_dep.name + ' will expire on ' + expire_date,
                'type': 'visa',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_dep_expire_date,
                'employee_id': emp_dep.employee_id.id,
                'type_of_document': 'Visa'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                
        for emp_dep in c_emp_dep_health_exps:  
            emp_dep_expire_date = emp_dep.healthcard_expire
            expire_date = datetime.strptime(emp_dep_expire_date, DEFAULT_SERVER_DATE_FORMAT)
            expire_date = expire_date.strftime(format_date)           
            exp_not = expiry_notify_obj.create({
                'name': 'Healthcard Expiry of : ' + emp_dep.name,
                'note': 'Healthcard of employee ' + emp_dep.name + ' will expire on ' + expire_date,
                'type': 'health',
                'date': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'expire_date': emp_dep_expire_date,
                'employee_id': emp_dep.employee_id.id,
                'type_of_document': 'Health Card'
            })            
            template_90.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
                
        for exp_not in e_emir_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_pass_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_visa_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        for exp_not in e_health_exps:  
            template_30.with_context(lang=self.env.user.lang).send_mail(exp_not.id, force_send=True, raise_exception=True)
        
        return True
