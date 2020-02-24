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

class Company(models.Model):
    _inherit = "res.company"
            
    @api.one
    @api.depends('company_month_start', 'company_day_start')
    def _compute_company_dates(self):
        curr_year_company_start_date = False
        if self.company_month_start and self.company_day_start:
            current_date = datetime.now()
            curr_year_company_start_date = current_date.replace(day=self.company_day_start, month=self.company_month_start)
            curr_year_company_start_date = curr_year_company_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.curr_year_company_start_date = curr_year_company_start_date
    
    company_month_start = fields.Selection([(1, 'January'), 
                                              (2, 'February'), 
                                              (3, 'March'), 
                                              (4, 'April'), 
                                              (5, 'May'), 
                                              (6, 'June'), 
                                              (7, 'July'), 
                                              (8, 'August'), 
                                              (9, 'September'), 
                                              (10, 'October'), 
                                              (11, 'November'), 
                                              (12, 'December')], 'Company Start Month', default=1, required=True)
    company_day_start = fields.Integer('Company Start Day', default=1, required=True)
    curr_year_company_start_date = fields.Date(string='Current Year Company Start Date', readonly=True, compute='_compute_company_dates')
    
    
    
    @api.one
    @api.constrains('company_month_start', 'company_day_start')
    def _company_start_check(self):
        company_month_start = self.company_month_start
        company_day_start = self.company_day_start   
        date_today = datetime.now()
        #company_month_date = date_today.replace(day=company_day_start, month=company_month_start)         
        if company_day_start < 1 or company_day_start > 31:
            raise ValidationError(_('The start day must be greater than 0 and less than 31.'))
        
    @api.multi
    def scheduler_recompute_number_of_days(self):     
        holiday_obj = self.env['hr.leave']       
        today = fields.Datetime.from_string(fields.Datetime.now())
        today = today.replace(hour=19, minute=59, second=59)
        today = fields.Datetime.to_string(today)           
        force_recompute = self.env.context.get('force_recompute', False)  
        domain = [('holiday_status_id.prorated', '=', True),
                  ('auto_allocated', '=', True),
                  ('number_of_days', '>', 0.0)]
        if not force_recompute:
            domain.append(('date_to', '>=', today))
        holidays = holiday_obj.search(domain)
        for holiday in holidays:
            holiday.recompute_given_fields()                    
        return True
    

    
