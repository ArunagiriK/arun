# -*- coding: utf-8 -*-

import logging
import math
import csv
import time
import pytz
from calendar import monthrange
from datetime import date, datetime, time as dt_time, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, rrule, MO, TU, WE, TH, FR, SA, SU

from odoo import api, fields, models, _
from odoo.addons.cw_hr_extended.models.hr_employee import to_naive_utc, to_tz
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_round

_logger = logging.getLogger(__name__)    

class HrHolidaysStatus(models.Model):
    _inherit = "hr.leave.type"  
    
    #To Do: Consider company? (Then code, type?, contract, etc)
    
    exclude_probation = fields.Boolean('Exclude in Probation?', default=True, help="Exclude this leave type from probation (means this leave type cannot take on a probation period).")
    exclude_rest_days = fields.Boolean('Exclude Rest Days', help="Exclude rest days from leave request count.")
    exclude_public_holidays = fields.Boolean('Exclude Public Holidays', help="Exclude public holidays from leave request count.")
    
    
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], 'Gender', help="If this leave type is include for selected gender only.")    
    country_id = fields.Many2one('res.country', 'Country', help="If this leave type is include for selected country only.")
    religion_id = fields.Many2one('res.religion', 'Religion', help="If this leave type is include for selected religion only")
    days = fields.Integer('No. of Days', help="No. of Days")     
    prorated = fields.Boolean('Prorated', help="If this leave type is a prorated (probably for annual leave type)")    
    exclude_future_holidays = fields.Boolean('Exclude Future Leave Requests', help="If this leave type is exclude for future prorated counts (Upto Date To in Leave Request).")
    limit_over_holidays = fields.Boolean('Limit Overlapping Leaves', help="Limit overlapping leaves on same range of dates on same department.")
    limit_days_type = fields.Boolean('Limit Days', default=True, help="Set maximum no of leaves taken per request")
    limit_future_dates = fields.Boolean('Limit Future Dates', default=True, help="Allow to take future dates up to certain conditions.")
    limit_future_type = fields.Selection([
                            ('day', 'Days'),
                            ('month', 'Months'),
                            ('year', 'Years'),
                            ], 'Limit Future Type', default='day')    
    limit_future_value = fields.Integer('Limit Future Value', default=365)
    double_validation = fields.Boolean(default=True)  
    carry_forward = fields.Boolean('Carry Forward')     
    type = fields.Selection([
                            ('annual', 'Annual Leave'),
                            ('compen', 'Compensatory'),
                            ('compas', 'Compassionate'),
                            ('unpaid', 'Unpaid'),
                            ('study', 'Study'),
                            ('sick', 'Sick'),
                            ('maternity', 'Maternity'),
                            ('paternity', 'Paternity'),
                            ('emergency', 'Emergency'),
                            ('haj', 'Haj'),
                            ('compan', 'Companion'),
                            ('training', 'Training'),
                            ('general', 'General')
                            ], 'Type', help="Types of leaves")
    
    apply_annual = fields.Selection([
                            ('annual_rule', 'Annual leave rule'),
                            #('schedule', 'Rest days'),
                            #('job', 'Job Position'),
                            #('depart', 'Department'),
                            ('contract', 'Contract'),
                            ('self', 'Days')
                            ], 'Annual Days Base', default='annual_rule', help="Compute Annual Leave Days based on this option")
    
    
    auto_allocate = fields.Boolean('Auto Allocate', default=True, help="Is it an auto allocated. Annual leave should auto allocate on anniversary date and others should on date set on company.")
    exclude_annual_leave_frst_yr = fields.Boolean('Exclude Allocation Annual Leave First Year', default=True, help="Exclude auto allocation of annual leave from first year of service.")
    exclude_leave_frst_yr = fields.Boolean('Exclude Leave First Year', help="This leave type cannot take on first year of service.")
    enable_per_service = fields.Boolean('Enable Per Service', help="No of times of leave request per service.") 
    no_per_service = fields.Integer('No. of Times/Service', default=1)
    
    annual_leave_rules = fields.Many2many('hr.annual.leave.rule', string='Annual Leave Rules', help='Apply an annual leave based on service years.')    
    marital = fields.Selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('divorced', 'Divorced')], 'Marital Type', help="If this leave type is include for selected marital status only")
    technical = fields.Boolean('Technical', default=False)
    code = fields.Char('Code', size=10, required=True)
    department_ids = fields.Many2many('hr.department', string='Departments', help='Departments for study leaves')
    job_ids = fields.Many2many('hr.job', string='Job Positions', domain="['|', ('department_id', 'in', department_ids and department_ids[0] and department_ids[0][2] or []), ('department_id', '=', False)]", help='Job Positions for study leaves')
    expire_on = fields.Selection([
                            ('comp_end', 'Company Administration End Date'),
                            ('ann_end', 'Anniversary End'),
                            ('var', 'Variable'),
                            ], 'Expire On', default='comp_end') 
    var_base = fields.Selection([
                            ('comp_start', 'Company Administration Start Date'),
                            ('ann_start', 'Anniversary Start'),
                            ], 'Variable Base')   
    expire_type = fields.Selection([
                            ('day', 'Days'),
                            ('month', 'Months'),
                            ('year', 'Years'),
                            ], 'Expire Type', default='day')    
    expire_value = fields.Integer('Expire Value', default=365)
    need_attachment = fields.Boolean('Need Attachment', help="Needs an attachment in order to confirm a leave request.")
    
    allocate_on = fields.Selection([
                            ('jan', 'January'),
                            ('feb', 'February'),
                            ('mar', 'March'),
                            ('apr', 'April'),
                            ('may', 'May'),
                            ('jun', 'June'),
                            ('jul', 'July'),
                            ('aug', 'August'),
                            ('sep', 'September'),
                            ('oct', 'October'),
                            ('nov', 'November'),
                            ('dec', 'December'),
                            ('ann', 'Anniversary'),
                            ('comp', 'Company Start'),
                            ], 'Allocate On', default='comp')
    
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code of the record must be unique!'),
    ]
    
    @api.multi
    @api.constrains('type')
    def _check_type(self):       
        for status in self:
            type = status.type
            if type in ['annual', 'sick']:         
                domain = [('id', '!=', status.id), ('type', '=', type)]
                nstatus = self.search_count(domain)
                if nstatus > 1:
                    raise ValidationError(_('You can not have 2 %s leave types!') %(type))
    
    
    @api.multi
    def get_days(self, employee_id):        
        #self.env.user.company_id.scheduler_recompute_number_of_days()
        result = super(HrHolidaysStatus, self).get_days(employee_id)        
        enable_prorated = self.env.context.get('enable_prorated', False)
        #To Do: If needed include draft both in search  and remove condition. eg: (('state', 'in', ['draft', 'clarify', 'verify', 'validate']),), (if holiday.state in ['draft', 'clarify', 'verify'])     
        holidays = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['clarify', 'verify', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])
        for holiday in holidays:
            status_dict = result[holiday.holiday_status_id.id]
            #~ if holiday.type == 'add':
            if holiday.state == 'validate' and enable_prorated and holiday.holiday_status_id.prorated:                        
                    #Removing Actual Allocation
                    status_dict['virtual_remaining_leaves'] -= holiday.number_of_days
                    status_dict['max_leaves'] -= holiday.number_of_days
                    status_dict['remaining_leaves'] -= holiday.number_of_days                       
                    #Adding Prorated Days
                    status_dict['virtual_remaining_leaves'] += holiday.prorated_days
                    status_dict['max_leaves'] += holiday.prorated_days
                    status_dict['remaining_leaves'] += holiday.prorated_days
            #~ elif holiday.type == 'remove':                        
                #Custom State Added which included
                #~ if holiday.state in ['clarify', 'verify']:
                    #~ status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
        return result
    
    
    
    
class HrHolidaysAnnualType(models.Model):
    _name = "hr.annual.leave.rule"
    _order = "sequence asc"
    _description = "Annual Leave Type"
        
    name = fields.Char(string='Name', required=True, copy=False)
    sequence = fields.Integer('Sequence', required=True, default=10)
    year_from = fields.Integer('Year From', required=True, default=0.0)
    year_to = fields.Integer('Year To', default=0.0)
    days = fields.Integer('No. of Days')
    
    @api.one
    @api.constrains('year_from', 'year_to')
    def _year_check(self):
        year_from = self.year_from
        year_to = self.year_to
        if year_to != 0.0 and year_from > year_to:
            raise ValidationError(_('The year to must be greater than year from.'))
    
    
    
    
