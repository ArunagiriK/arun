# -*- coding: utf-8 -*-
#
#################################################################################
# Author      : Codeware Computer Trading L.L.C. (<www.codewareuae.com>)
# Copyright(c): 2017-Present Codeware Computer Trading L.L.C.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import logging
import time
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError

_logger = logging.getLogger(__name__)

inactive_hr_models = [
('hr.recruitment.request', ''),
('hr.probation.review', ''),
('advance.request.form', ''),
('hr.request', ''),
('hr.applicant', ''),
('hr.contract', ''),
('hr.holidays', ''),
('hr.attendance', ''),
('hr.expiry.notification', ''),
('hr.gratutity', ''),
('hr.probation.notification', ''),
('hr.profile.update', ''),
('hr.expense.request', ''),
('employee.expenses.request', ''),
('hr.expense', ''),
('hr.expense.sheet', ''),
('employee.advance', ''),
('cw.employee.salary.advance', ''),
('orientation.request', ''),
('hr.payslip', ''),
('employee.orientation', ''),
('hr.employee.document', ''),
('employee.checklist', ''),
('employee.training', ''),
]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def in_active_record(self, model_name, field_name):
        for emp in self:
            self.env[model_name].search([(field_name, '=', emp.id)]).write({'active': False})
        return True

    @api.multi
    def relived(self):
        for emp in self:
            if emp.salary_advance_balance > 0.0:
                raise ValidationError(_('This employee have pending advances (%s).' % (emp.salary_advance_balance)))        
        for in_active_hr in inactive_hr_models:
            hr_model = in_active_hr[0]
            hr_model_field = in_active_hr[1]
            hr_fields = self.env['ir.model.fields'].search([('ttype', 'in', ['many2one']), 
                                            ('relation', '=', 'hr.employee'),
                                            ('model_id.model', '!=', 'hr.employee'),
                                            ('model_id.model', '=', hr_model),
                                            ('model_id.transient', '=', False)])            
            for hr_field in hr_fields:
                field_name = hr_field.name
                self.in_active_record(model_name=hr_model, field_name=field_name)    
            #self.in_active_record(model_name=hr_model, field_name=hr_model_field)         
        result = super(HrEmployee, self).relived()
        return result

    @api.multi
    def terminate(self):
        for emp in self:
            if emp.salary_advance_balance > 0.0:
                raise ValidationError(_('This employee have pending advances (%s).' % (emp.salary_advance_balance)))        
        for in_active_hr in inactive_hr_models:
            hr_model = in_active_hr[0]
            hr_model_field = in_active_hr[1]
            hr_fields = self.env['ir.model.fields'].search([('ttype', 'in', ['many2one']), 
                                            ('relation', '=', 'hr.employee'),
                                            ('model_id.model', '!=', 'hr.employee'),
                                            ('model_id.model', '=', hr_model),
                                            ('model_id.transient', '=', False)])            
            for hr_field in hr_fields:
                field_name = hr_field.name
                self.in_active_record(model_name=hr_model, field_name=field_name)   
            #self.in_active_record(model_name=hr_model, field_name=hr_model_field)
        result = super(HrEmployee, self).terminate()
        return result

    @api.multi
    def in_active_emp(self):
        for emp in self:
            if emp.salary_advance_balance > 0.0:
                raise ValidationError(_('This employee have pending advances (%s).' % (emp.salary_advance_balance)))        
        for in_active_hr in inactive_hr_models:
            hr_model = in_active_hr[0]
            hr_model_field = in_active_hr[1]
            hr_fields = self.env['ir.model.fields'].search([('ttype', 'in', ['many2one']), 
                                            ('relation', '=', 'hr.employee'),
                                            ('model_id.model', '!=', 'hr.employee'),
                                            ('model_id.model', '=', hr_model),
                                            ('model_id.transient', '=', False)])            
            for hr_field in hr_fields:
                field_name = hr_field.name
                self.in_active_record(model_name=hr_model, field_name=field_name)    
            #self.in_active_record(model_name=hr_model, field_name=hr_model_field)            
            stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                    ('state', '=', 'employment')])        
            if stage_obj:
                stage_obj.sudo().write({'end_date': date.today()})
            else:
                self.stages_history.search([('employee_id', '=', self.id),
                                            ('state', '=', 'grounding')]).sudo().write({'end_date': date.today()})
            #self.stages_history.sudo().create({'end_date': date.today(),
            #                                   'employee_id': self.id,
            #                                   'state': 'employment'})
        return True

