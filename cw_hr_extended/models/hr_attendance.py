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

class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    
    @api.one
    @api.depends('name', 'employee_id', 'check_in', 'check_out')
    def _compute_hours(self):
        self.worked_hours = 0.0  
        self.sch_hours = 0.0 
        self.diff_hours = 0.0
        self.eligible_diff_hours = 0.0
        self.late_sigin_hours = False
        self.late_signout_hours = False
        self.late_sigin_hours_display = False
        self.late_signout_hours_display = False
        sch_date_start = False
        sch_date_end = False
        exclude_late_signin = self.employee_id and self.employee_id.exclude_late_signin or False 
        exclude_late_signout = self.employee_id and self.employee_id.exclude_late_signout or False
        name = datetime.strptime(self.name, DEFAULT_SERVER_DATETIME_FORMAT)        
        working_hrs = 0
        employee = self.sudo(SUPERUSER_ID).employee_id
        if employee and employee.contract_id and employee.contract_id.working_hrs:
            working_hrs = float(employee.contract_id.working_hrs)
        if self.employee_id and self.contract_id:
            if self.contract_id.resource_calendar_id:
            
            if self.sch_date_start:
                sch_date_start = datetime.strptime(self.sch_date_start, DEFAULT_SERVER_DATETIME_FORMAT)  
            if self.sch_date_end:
                sch_date_end = datetime.strptime(self.sch_date_end, DEFAULT_SERVER_DATETIME_FORMAT)              
            if self.action == 'sign_in' and sch_date_start:
                late_signin_hours_datetime = (sch_date_start - name)
                self.late_sigin_hours = ((late_signin_hours_datetime.total_seconds()) / 60.0)/60.00
                late_sigin_hours_display = False
                if name > sch_date_start:
                    late_signin_hours_datetime = (name - sch_date_start)
                    late_sigin_hours_display = '- ' + str(late_signin_hours_datetime)
                else:
                    late_signin_hours_datetime = (sch_date_start - name)
                    late_sigin_hours_display = '+ ' + str(late_signin_hours_datetime)                
                self.late_sigin_hours_display = late_sigin_hours_display 
            if sch_date_start and sch_date_end and not self.on_call:
                sch_hours_datetime = (sch_date_end - sch_date_start)
                self.sch_hours = ((sch_hours_datetime.total_seconds()) / 60) / 60.0
        if self.action == 'sign_out':
            last_signin = self.search([
                ('employee_id', '=', self.employee_id.id),
                ('name', '<', self.name), ('action', '=', 'sign_in')
            ], limit=1, order='name DESC')
            last_signout = self.search([
                ('employee_id', '=', self.employee_id.id),
                ('name', '<', self.name), ('action', '=', 'sign_out')
            ], limit=1, order='name DESC')
            last_signin_datetime = False
            last_signout_datetime = False
            for sign_in in last_signin:
                last_signin_datetime = datetime.strptime(sign_in.name, DEFAULT_SERVER_DATETIME_FORMAT)
                if sign_in.schedule_detail_id:
                    if sign_in.sch_date_start:
                        sch_date_start = datetime.strptime(sign_in.sch_date_start, DEFAULT_SERVER_DATETIME_FORMAT)  
            for sign_out in last_signout:
                last_signout_datetime = datetime.strptime(sign_out.name, DEFAULT_SERVER_DATETIME_FORMAT)
            if last_signin_datetime:
                workedhours_datetime = (name - last_signin_datetime)
                self.worked_hours = ((workedhours_datetime.total_seconds()) / 60) / 60.0                
                if sch_date_start:
                    late_sigin_hours_display = False                
                    if last_signin_datetime > sch_date_start:
                        late_signin_hours_datetime = (last_signin_datetime - sch_date_start)
                        late_sigin_hours_display = '- ' + str(late_signin_hours_datetime)
                    else:
                        late_signin_hours_datetime = (sch_date_start - last_signin_datetime)
                        late_sigin_hours_display = '+ ' + str(late_signin_hours_datetime)                
                    self.late_sigin_hours_display = late_sigin_hours_display                
                if last_signout_datetime and last_signout_datetime > last_signin_datetime:
                    self.worked_hours = 0.0
                    self.late_sigin_hours = False                
                    self.late_sigin_hours_display = False            
            if not self.schedule_detail_id and self.sch_hours == 0.0 and working_hrs > 0.0:
                req_date = self._get_date_employee_tz(self.employee_id.id, self.name)                              
                r_date_from = req_date + " 00:00:00"
                r_date_to = req_date + " 23:59:59"
                rest_day = False                
                r_date = datetime.strptime(req_date, DEFAULT_SERVER_DATE_FORMAT)
                employee_id = self.employee_id.id
                rest_days = self.env['hr.schedule.restday.detail'].sudo(SUPERUSER_ID).search([                            
                            ('rest_schedule_id.employee_id', '=', employee_id),
                            ('rest_schedule_id.state', '=', 'validate'),
                            ('rest_schedule_id.on_call', '=', False), 
                            ('day', '=', req_date)])
                schedule_days = self.env['hr.schedule.detail'].sudo(SUPERUSER_ID).search([                            
                            ('schedule_id.employee_id', '=', employee_id),
                            ('schedule_id.state', '=', 'validate'),
                            ('schedule_id.on_call', '=', False),                            
                            ('employee_id', '=', employee_id),
                            ('state', '=', 'validate'),
                            ('on_call', '=', False),
                            ('day', '=', req_date)]) 
                if not schedule_days: 
                    if rest_days:
                        rest_day = True
                    else:
                        rest_day_dates = self._get_rest_day_dates(employee_id, req_date, req_date)
                        if r_date in rest_day_dates:
                            rest_day = True
                if req_date == '2017-09-28' and employee_id == 44:
                    print "self.employee_id",self.employee_id.name
                    print "req_date",req_date
                    print "schedule_days",schedule_days
                    print "rest_days",rest_days
                    print "rest_day",rest_day
                    
                if not rest_day:
                    self.sch_hours = working_hrs
            if self.sch_hours > 0.0 and self.worked_hours > 0.0:
                self.diff_hours = self.worked_hours - self.sch_hours
                if self.diff_hours > 1.0:
                    self.eligible_diff_hours = self.diff_hours
            #if self.worked_hours > 24:
            #    self.worked_hours = 0.0
            #    self.late_sigin_hours = False
            if sch_date_end:
                #late_signout_hours_datetime = (name - sch_date_end)
                late_signout_hours_datetime = (sch_date_end - name)
                self.late_signout_hours = ((late_signout_hours_datetime.total_seconds()) / 60) / 60.0
                late_signout_hours_display = False              
                if name > sch_date_end:
                    late_signout_hours_datetime = (name - sch_date_end)                        
                    late_signout_hours_display = '- ' + str(late_signout_hours_datetime)
                else:                        
                    late_signout_hours_datetime = (sch_date_end - name)                       
                    late_signout_hours_display = '+ ' + str(late_signout_hours_datetime) 
                self.late_signout_hours_display = late_signout_hours_display                          
        if exclude_late_signin or self.on_call:
            self.late_sigin_hours = False   
            self.late_sigin_hours_display = False    
        if exclude_late_signout or self.on_call:
            self.late_signout_hours = False
            self.late_signout_hours_display = False 
        
    
    last_action = fields.Many2one("hr.attendance", string="Last Action", compute='_compute_last_action', readonly=True)
    #worked_hours = fields.Float(compute='_compute_hours', string='Worked Hours', store=False, readonly=True)
    #sch_hours = fields.Float(compute='_compute_hours', string='Scheduled Hours', store=False, readonly=True)
    #diff_hours = fields.Float(compute='_compute_hours', string='Overtime', store=False, readonly=True)
    #late_sigin_hours = fields.Char(compute='_compute_hours', string='Late Sigin Hours', store=True, readonly=True)
    #late_signout_hours = fields.Char(compute='_compute_hours', string='Late Signout Hours', store=True, readonly=True)
    worked_hours = fields.Float(compute='_compute_hours', string='Worked Hours', store=True, readonly=True)
    sch_hours = fields.Float(compute='_compute_hours', string='Scheduled Hours', store=True, readonly=True)
    diff_hours = fields.Float(compute='_compute_hours', string='Overtime', store=True, readonly=True)
    eligible_diff_hours = fields.Float(compute='_compute_hours', string='Eligible Overtime', store=True, readonly=True)
    late_sigin_hours = fields.Float(compute='_compute_hours', string='Late Sigin Hours', store=True, readonly=True)
    late_signout_hours = fields.Float(compute='_compute_hours', string='Late Signout Hours', store=True, readonly=True)
    late_sigin_hours_display = fields.Char(compute='_compute_hours', string='Late Sigin Display Hours', store=True, readonly=True)
    late_signout_hours_display = fields.Char(compute='_compute_hours', string='Late Signout Display Hours', store=True, readonly=True)
    
    @api.model
    def _get_date_employee_tz(self, employee_id, date):
        employee = self.env['hr.employee']

        tz = False
        if employee_id:
            emp = employee.browse(employee_id)
            tz = emp.user_id.partner_id.tz

        if not date:
            date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        cal_tz = timezone(tz or 'utc')

        given_dt = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        given_tz_dt = pytz.utc.localize(given_dt)
        given_tz_dt = given_tz_dt.astimezone(cal_tz)
        given_tz_date_str = datetime.strftime(given_tz_dt, DEFAULT_SERVER_DATE_FORMAT)
        return given_tz_date_str

    @api.model
    def _get_rest_day_dates(self, employee_id, from_date, to_date):
        rest_day_dates = []
        #res = 0
        employee = self.env['hr.employee'].browse(employee_id)
        if employee and employee.contract_id \
            and employee.contract_id.schedule_template_id \
            and employee.contract_id.schedule_template_id.restday_ids \
            and from_date and to_date:            
            from_date = datetime.strptime(from_date, DEFAULT_SERVER_DATE_FORMAT)
            to_date = datetime.strptime(to_date, DEFAULT_SERVER_DATE_FORMAT)
            restday_ids = employee.contract_id.schedule_template_id.restday_ids
            restdays = []
            for wday in restday_ids:
                if wday.name.lower() == 'sunday':
                    restdays.append(SU)
                elif wday.name.lower() == 'monday':
                    restdays.append(MO)
                elif wday.name.lower() == 'tuesday':
                    restdays.append(TU)
                elif wday.name.lower() == 'wednesday':
                    restdays.append(WE)
                elif wday.name.lower() == 'thursday':
                    restdays.append(TH)
                elif wday.name.lower() == 'friday':
                    restdays.append(FR)
                elif wday.name.lower() == 'saturday':
                    restdays.append(SA)
            #res = rrule(DAILY, dtstart=from_date, until=to_date, byweekday=restdays).count()
            rest_day_dates = rrule(DAILY, dtstart=from_date, until=to_date, byweekday=restdays)
        rest_day_dates = [rest_day for rest_day in rest_day_dates]
        return rest_day_dates
    
    
class hr_contract(models.Model): 
    _inherit = 'hr.contract'
        
    working_hrs = fields.Float(string='Working Hrs', default=7) # See overtime for details
    
    
class hr_holidays(models.Model):
    _inherit = "hr.leave"    
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['initial', 'draft', 'cancel', 'confirm']:
                raise UserError(_('You cannot delete a leave which is in %s state.') % (rec.state,))
        return models.Model.unlink(self)
    
    
    
    
    
    
    
    
    
    
    
    
    
       
