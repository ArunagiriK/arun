# -*- coding: utf-8 -*-

import logging
import time
import math
import csv
from calendar import monthrange
from datetime import date
from datetime import datetime
from datetime import timedelta
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, rrule, MO, TU, WE, TH, FR, SA, SU

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    @api.multi
    @api.depends('employee_id', 'employee_id.gender', 'employee_id.marital', 'employee_id.religion_id', 'employee_id.country_id', 
                 'employee_id.department_id', 'employee_id.job_id', 'employee_id.grade_id')
    def _get_holiday_status_domain(self):        
        for record in self:
            employee_id = record.employee_id and record.employee_id.id or False
            hr_holiday_status_ids = self.employee_leave_types(employee_id)
            hr_holiday_status_domain_ids = self.env['hr.leave.type']
            if hr_holiday_status_ids:
                hr_holiday_status = self.env['hr.leave.type'].browse(hr_holiday_status_ids)
                hr_holiday_status_domain_ids =  hr_holiday_status           
            record.update({
                'hr_holiday_status_domain_ids': hr_holiday_status_domain_ids,
            })
            
    @api.multi
    def _compute_annual_days(self):
        for contract in self:
            #annual_days = contract.annual_leave_days
            #annual_leave_types = contract.hr_holiday_status_ids.filtered(lambda r: r.type == 'annual' and r.apply_annual == 'annual_rule' and r.technical == False)
            annual_leave_types = contract.hr_holiday_status_ids.filtered(lambda r: r.type == 'annual' and r.technical == False)
            number_of_days = 0.0
            for annual_leave_type in annual_leave_types:
                if annual_leave_type.apply_annual == 'annual_rule':
                    join_date = contract.employee_id.join_date
                    if join_date:
                        join_d = datetime.datetime.strptime(str(join_date), "%Y-%m-%d")
                        date_today = datetime.datetime.now() 
                        date_today = date_today.replace(hour=00, minute=00, second=00)
                        num_of_years = relativedelta(date_today, join_d).years
                        annual_leave_rule = annual_leave_type.annual_leave_rules.filtered(lambda r: r.year_from <= num_of_years <= r.year_to)
                        if not annual_leave_rule:
                            annual_leave_rule = annual_leave_type.annual_leave_rules.filtered(lambda r: r.year_from <= num_of_years and r.year_to == 0.0)
                        if annual_leave_rule:
                            number_of_days +=  sum(annual_leave_rule.mapped('days'))
                elif annual_leave_type.apply_annual == 'contract':
                    number_of_days +=  contract.annual_leave_days
                elif annual_leave_type.apply_annual == 'self':
                    number_of_days +=  sum(annual_leave_type.mapped('days'))
            contract.annual_days = number_of_days    
    
    hr_holiday_status_domain_ids = fields.Many2many('hr.leave.type', string='Domain Leave Types', readonly=True)    
    #hr_holiday_status_ids = fields.Many2many('hr.holidays.status', string='Leave Types', domain="[('id','in', hr_holiday_status_domain_ids and hr_holiday_status_domain_ids[0] and hr_holiday_status_domain_ids[0][2] or [False])]", required=True)
    hr_holiday_status_ids = fields.Many2many('hr.leave.type', 'contract_holi_status_rel', 'contract_id', 'holi_status_id', string="Leave Types", copy=False, required=True)
    annual_leave_days = fields.Integer('No. of Annual Leave Days')
    annual_days = fields.Float('Annual Leave Days', compute='_compute_annual_days')
      
    
    
    
    leave_alloc_lines = fields.One2many('hr.leave.allocation', 'contract_id', 'Leave Allocations')
            
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            employee_id = self.employee_id.id
            hr_holiday_status_ids = self.employee_leave_types(employee_id)
            if hr_holiday_status_ids:
                hr_holiday_status = self.env['hr.leave.type'].browse(hr_holiday_status_ids)
                self.hr_holiday_status_ids = hr_holiday_status
        res = super(HrContract, self)._onchange_employee_id()
        return res
    
    
    @api.model
    def employee_leave_types(self, employee_id):
        status_ids = []            
        if not employee_id:
            return False
        else:
            emp = self.env['hr.employee'].sudo(SUPERUSER_ID).browse(employee_id)
            emp_gender = emp.gender
            emp_marital = emp.marital
            emp_religion_id = emp.religion_id and emp.religion_id.id or False
            emp_country_id = emp.country_id and emp.country_id.id or False
            emp_department_id = emp.department_id and emp.department_id.id or False
            emp_job_id = emp.job_id and emp.job_id.id or False
            emp_grade_id = emp.grade_id and emp.grade_id.id or False
            for rec in self.env['hr.leave.type'].search([('technical', '=', False)]):
                if rec.gender and rec.religion_id and rec.marital:
                    if rec.gender == emp_gender and \
                    rec.religion_id.id == emp_religion_id and \
                    rec.marital == emp_marital:
                        status_ids.append(rec.id)
                elif rec.gender and rec.marital:
                    if rec.gender == emp_gender and rec.marital == emp_marital:
                        status_ids.append(rec.id)
                elif rec.gender:
                    if rec.gender == emp_gender:
                        status_ids.append(rec.id)
                elif rec.religion_id:
                    if rec.religion_id.id == emp_religion_id:
                        status_ids.append(rec.id)
                elif rec.marital:
                    if rec.marital == emp_marital:
                        status_ids.append(rec.id)
                elif rec.country_id:
                    if rec.country_id.id == emp_country_id:
                        status_ids.append(rec.id)
                elif rec.type == 'study':
                    department_ids = [br.id for br in rec.department_ids]
                    job_ids = [br.id for br in rec.job_ids]
                    if job_ids:
                        if emp_job_id in job_ids:
                            status_ids.append(rec.id)
                    else:
                        if emp_department_id in department_ids:
                            status_ids.append(rec.id)
                elif rec.type == 'annual' and emp.department_id and not emp.department_id.exclude_annual_leave:                    
                    status_ids.append(rec.id)
                else:
                    status_ids.append(rec.id)     
            return status_ids
        
        
