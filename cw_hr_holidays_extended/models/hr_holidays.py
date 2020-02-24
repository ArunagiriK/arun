# -*- coding: utf-8 -*-

import logging
import math
import csv
import time
import pytz
from werkzeug import url_encode
from calendar import monthrange
from datetime import date, datetime, time as dt_time, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, rrule, MO, TU, WE, TH, FR, SA, SU

from odoo import api, fields, models, _
from odoo.addons.cw_hr_extended.models.hr_employee import to_naive_utc, to_tz
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_round, float_compare
#from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

class HrHolidays(models.Model):
    _name = "hr.leave"
    _inherit = ['hr.leave', 'mail.thread', 'ir.model.role', 'common.clarify']
    _employee_id = 'employee_id'
    
    #def _get_column_user_id(self):
    #    return self._columns['employee_id'].user_id
    
    #_employee_id = lambda self: self._get_column_employee_id()    
    #_user_id = lambda self: self._get_column_user_id()

    def _default_contract(self):
        employee_id = self.env.context.get('default_employee_id', False)
        contract_id = self.env['hr.contract']
        if employee_id:
            employee = self.env['hr.employee'].search([('id', '=', employee_id)], limit=1)
            contract_id =  employee and employee.contract_id or self.env['hr.contract']
        return contract_id
    
    
    @api.multi
    @api.depends('holiday_status_id', 'employee_id', 'contract_id', 'contract_id.resource_calendar_id',
                 'holiday_status_id.exclude_rest_days', 
                 'holiday_status_id.exclude_public_holidays',
                 'number_of_days', 'date_from', 'date_to')
    def _compute_days(self):        
        for record in self:
            number_of_public_holidays = 0.0
            number_of_rest_days = 0.0
            number_of_holidays = 0.0
            if record.date_from and record.date_to and record.holiday_status_id and record.employee_id:            
                date_from = record.date_from
                date_to = record.date_to
                employee = record.employee_id
                status = record.holiday_status_id
                date_from = fields.Date.from_string(date_from)
                date_to = fields.Date.from_string(date_to)
                date_dt = date_from
                while date_dt <= date_to:
                    if not employee.work_scheduled_on_day(
                            date_dt,
                            status.exclude_public_holidays,
                            False,
                    ):
                        number_of_public_holidays += 1                        
                    if not employee.work_scheduled_on_day(
                            date_dt,
                            False,
                            status.exclude_rest_days,
                    ):
                        number_of_rest_days += 1
                    if not employee.work_scheduled_on_day(
                            date_dt,
                            status.exclude_public_holidays,
                            status.exclude_rest_days,
                    ):
                        number_of_holidays += 1
                    date_dt += relativedelta(days=1)  
            record.update({
                'number_of_public_holidays': number_of_public_holidays,
                'number_of_rest_days': number_of_rest_days,
                'number_of_holidays': number_of_holidays,
            })            
            
    #~ @api.multi
    #~ def _compute_prorated_days(self):
        #~ for holiday in self:
            #~ number_of_days_temp = holiday.number_of_days_temp
            #~ prorated_days = number_of_days_temp
            #~ if holiday.type == 'add' and \
                #~ holiday.auto_allocated and \
                #~ holiday.holiday_status_id and \
                #~ holiday.holiday_status_id.prorated and number_of_days_temp > 0.0:                                
                #~ date_today = datetime.now()                
                #~ date_today = date_today.replace(hour=00, minute=00, second=00)
                #~ date_from = holiday.date_from
                #~ date_to = holiday.date_to
                #~ if date_from and date_to:
                    #~ date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
                    #~ date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
                    #~ if date_today >= date_to:
                        #~ prorated_days = number_of_days_temp
                    #~ elif date_today < date_from:
                        #~ prorated_days = 0.0                        
                    #~ elif date_from <= date_today <= date_to:
                        #~ total_day_diff = date_to - date_from
                        #~ total_days = float(total_day_diff.days)
                        #~ daily_allocate = float(number_of_days_temp / total_days)
                        #~ prorate_day_diff = date_today - date_from
                        #~ total_prorate_days = float(prorate_day_diff.days)
                        #~ prorated_days = float(daily_allocate * total_prorate_days)
            #~ holiday.prorated_days = prorated_days            
            
    @api.multi
    def _compute_future_prorated_days(self):
        for holiday in self:
            future_prorated_days = 0.0
            if holiday.date_to and \
                holiday.holiday_status_id and \
                holiday.holiday_status_id.prorated and not holiday.holiday_status_id.exclude_future_holidays:                                
                
                contract = holiday.contract_id 
                date_today = datetime.now()                
                date_today = date_today.replace(hour=00, minute=00, second=00)                
                tomorrow_date = date_today + timedelta(days=1) 
                
                date_end = contract.date_end
                date_to = fields.Datetime.from_string(holiday.date_to)
                date_end = date_end and datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT) or False
                if date_end and date_to and date_to > date_end:
                    date_to = date_end
                    
                given_date = fields.Datetime.to_string(date_to)
                from_date = fields.Datetime.to_string(tomorrow_date)                
                future_prorated_days = self.calculate_prorated_given_date(from_date, given_date, contract)
            holiday.future_prorated_days = future_prorated_days            
            
    @api.multi
    def _compute_common_prorated_days(self):
        for holiday in self:
            dateto_prorated_days = 0.0
            virtual_prorated_days = 0.0
            remaining_prorated_days = 0.0
            if holiday.date_to and \
                holiday.holiday_status_id and \
                holiday.holiday_status_id.prorated and not holiday.holiday_status_id.exclude_future_holidays:
                virtual_remaining_leaves = holiday.holiday_status_id.with_context(enable_prorated=True, employee_id=holiday.employee_id.id).virtual_remaining_leaves
                leave_days = holiday.holiday_status_id.with_context(enable_prorated=True).get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
                remaining_leaves = leave_days['remaining_leaves']
                virtual_remaining_leaves = leave_days['virtual_remaining_leaves']                
                future_prorated_days = holiday.future_prorated_days
                remaining_prorated_days = remaining_leaves      
                virtual_prorated_days = virtual_prorated_days                    
                dateto_prorated_days = virtual_remaining_leaves + future_prorated_days
            holiday.remaining_prorated_days = remaining_prorated_days
            holiday.virtual_prorated_days = virtual_prorated_days
            holiday.dateto_prorated_days = dateto_prorated_days

    #~ @api.multi
    #~ @api.depends('number_of_days_temp',  'auto_allocated', 'holiday_status_id.prorated')
    #~ def _compute_number_of_days(self):        
        #~ super(HrHolidays, self)._compute_number_of_days()
        #~ for holiday in self:
            #~ if holiday.type == 'add' and \
                #~ holiday.auto_allocated and \
                #~ holiday.holiday_status_id and \
                #~ holiday.holiday_status_id.prorated and holiday.number_of_days_temp > 0.0:              
                #~ holiday.number_of_days = holiday.prorated_days
    
    
    @api.multi
    @api.depends('holiday_status_id', 'employee_id', 
                 'holiday_status_id', 'holiday_status_id.limit_over_holidays',
                 'department_id', 'department_id.overlapping_leaves', 
                 'date_from', 'date_to')
    def _compute_waiting_list_no(self):
        for holiday in self:
            waiting_list_no = 0
            if holiday.state not in ['draft', 'cancel']:
                overlapping_leaves = self.search([
                    #('id', '!=', holiday.id),
                    ('state', 'not in', ['draft', 'refuse', 'cancel']),
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('department_id', '=', holiday.department_id.id),
                    ('holiday_status_id', '=', holiday.holiday_status_id.id),
                    ('holiday_status_id.limit_over_holidays', '=', True)
                ])
                n_overlapping_leaves = len(overlapping_leaves) - 1
                if n_overlapping_leaves > 0 and \
                    holiday.department_id.overlapping_leaves > 0 and \
                    n_overlapping_leaves >= holiday.department_id.overlapping_leaves: 
                    waiting_list_no = sum(overlapping_leaves.mapped('waiting_list_no')) + 1        
            holiday.waiting_list_no = waiting_list_no
            
            
    @api.multi
    def _get_attached_docs(self):
        attachment = self.env['ir.attachment']
        for holi in self:
            holi_attachments = attachment.search([('res_model', '=', 'hr.leave'), ('res_id', '=', holi.id)], count=True)
            holi.doc_count = holi_attachments or 0
                
        
    technical = fields.Boolean('Technical')     
    contract_id = fields.Many2one('hr.contract', 'Contract', default=_default_contract)
    state = fields.Selection([
                            ('draft', 'To Submit'),
                            ('clarify', 'Under Clarify'),
                            ('cancel', 'Cancelled'),
                            ('confirm', 'Confirmed'),
                            ('refuse', 'Refused'),
                            ('verify', 'Verified'),
                            ('validate1', 'Validated'),
                            ('validate', 'Approved')
                            ], default='draft')
    #~ half_day = fields.Boolean('Half Day', readonly=True, copy=False, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=False)
    
    number_of_public_holidays = fields.Float('Number of Public Holidays', compute='_compute_days', store=True)
    number_of_rest_days = fields.Float('Number of Rest Days', compute='_compute_days', store=True) 
    number_of_holidays = fields.Float('Number of Holidays Days', compute='_compute_days', store=True) 
    prorated_days = fields.Float('Prorated Days')
    #~ number_of_days = fields.Float(compute='_compute_number_of_days') 
    future_prorated_days = fields.Float('Future Prorated Days', compute='_compute_future_prorated_days')
    virtual_prorated_days = fields.Float('Virtual Prorated Days', compute='_compute_common_prorated_days')
    remaining_prorated_days = fields.Float('Remaining Days', compute='_compute_common_prorated_days')
    dateto_prorated_days = fields.Float('Prorated Days (Date To (C))', compute='_compute_common_prorated_days')
    waiting_list_no = fields.Integer('Waiting List Number', compute='_compute_waiting_list_no', store=True)
    doc_count = fields.Integer(compute='_get_attached_docs', string="Number of documents attached")
    auto_allocated = fields.Boolean(string="Auto Allocated", default=False, copy=False)
    allocate_daily = fields.Boolean(string="Allocate Daily", default=False, copy=False)
    expired_remove_rec = fields.Boolean(string="Expired Remove Rec", default=False, copy=False)
    other_remove_rec = fields.Boolean(string="Other Remove Rec", default=False, copy=False)
    
    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for holiday in self:
            if not holiday.technical:
                domain = [
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('employee_id', '=', holiday.employee_id.id),
                    ('id', '!=', holiday.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                ]
                nholidays = self.search_count(domain)
                if nholidays:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))

    #~ @api.constrains('state', 'number_of_days')
    #~ def _check_holidays(self):
        #~ for holiday in self:
            #~ if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id or holiday.technical:
                #~ continue
            #~ leave_days = holiday.holiday_status_id.with_context(enable_prorated=True).get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
            #~ if holiday.holiday_status_id.prorated and not holiday.holiday_status_id.exclude_future_holidays and holiday.future_prorated_days > 0.0:
                #~ future_prorated_days = holiday.future_prorated_days
                #~ leave_days['remaining_leaves'] += future_prorated_days
                #~ leave_days['virtual_remaining_leaves'] += future_prorated_days
            #~ if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
              #~ float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                #~ raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        #~ 'Please verify also the leaves waiting for validation.'))

    #~ @api.constrains('state', 'number_of_days')
    #~ def _check_limit_days_type(self):
        #~ for holiday in self:
            #~ if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id  or holiday.technical:
                #~ continue
            #~ if holiday.holiday_status_id.limit_days_type:
                #~ days = holiday.holiday_status_id.days
                #~ if holiday.holiday_status_id.type == 'annual':
                    #~ contract = holiday.contract_id 
                    #~ days = contract.annual_days
                #~ if holiday.number_of_days > days:
                    #~ raise ValidationError(_('The number of days applied is exceeding than the allowed limit.'))

    @api.constrains('state', 'holiday_status_id', 'date_from', 'date_to')
    def _check_limit_future_dates(self):
        for holiday in self:
            if holiday.holiday_type != 'employee' or holiday.technical:
                continue
            if  holiday.holiday_status_id.limit_future_dates:
                holiday_status = holiday.holiday_status_id
                date_from = fields.Datetime.from_string(holiday.date_from)
                date_to = fields.Datetime.from_string(holiday.date_to)                                
                #future_date = fields.Datetime.from_string(fields.Datetime.now())
                future_date = datetime.now()                
                future_date = future_date.replace(hour=00, minute=00, second=00)                
                #future_date = future_date + timedelta(days=1)                
                if holiday_status.limit_future_type == 'day':
                    future_date = future_date + timedelta(days=holiday_status.limit_future_value)
                elif holiday_status.limit_future_type == 'month':
                    future_date = future_date + relativedelta(months=+holiday_status.limit_future_value)
                elif holiday_status.limit_future_type == 'year':
                    future_date = future_date + relativedelta(years=+holiday_status.limit_future_value)
                if date_from > future_date or date_to > future_date:
                    raise ValidationError(_('The start and end date must be less than %s %s(s) from today.') % (holiday_status.limit_future_value, holiday_status.limit_future_type))
                
    
    @api.constrains('holiday_status_id', 'date_from', 'date_to', 'employee_id')
    def _check_probation_period_status(self):
        for holiday in self:            
            if not holiday.technical and \
               holiday.employee_id and holiday.contract_id and \
               holiday.holiday_status_id and holiday.holiday_status_id.exclude_probation:            
               emp_current_contract = holiday.contract_id
               trial_date_start = emp_current_contract and emp_current_contract.trial_date_start or False
               trial_date_end = emp_current_contract and emp_current_contract.trial_date_end or False
               date_from = holiday.date_from
               date_to = holiday.date_to
               if trial_date_start and trial_date_end and date_from and date_to:
                    trial_date_start = datetime.strptime(trial_date_start, DEFAULT_SERVER_DATE_FORMAT)
                    trial_date_end = datetime.strptime(trial_date_end, DEFAULT_SERVER_DATE_FORMAT)
                    date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
                    date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
                    if date_from <= trial_date_end:
                        raise ValidationError(_('The leave type applied is not applicable for probation period!')) 
                
                
    @api.constrains('holiday_status_id', 'date_from', 'date_to', 'employee_id')
    def _check_leave_frst_yr(self):
        for holiday in self:            
            if not holiday.technical and \
               holiday.employee_id and \
               holiday.holiday_status_id and holiday.holiday_status_id.exclude_leave_frst_yr: 
               first_anniversary_date = fields.Date.from_string(holiday.employee_id.first_anniversary_date)
               date_from = fields.Datetime.from_string(holiday.date_from)
               date_to = fields.Datetime.from_string(holiday.date_to)
               if date_from < first_anniversary_date or date_to < first_anniversary_date:
                    raise ValidationError(_('This leave type (%s) is eligble only after one year of service!') % (holiday.holiday_status_id.name)) 
                
                
    @api.constrains('holiday_status_id', 'employee_id')
    def _check_leave_per_service(self):
        for holiday in self:            
            if not holiday.technical and \
               holiday.employee_id and \
               holiday.holiday_status_id and holiday.holiday_status_id.enable_per_service:                
               domain = [
                    ('employee_id', '=', holiday.employee_id.id),
                    ('id', '!=', holiday.id),
                    ('holiday_status_id', '=', holiday.holiday_status_id.id),
                    ('holiday_status_id.enable_per_service', '=', holiday.holiday_status_id.enable_per_service),
                    ('state', 'not in', ['cancel', 'refuse']),
                ]
               nholidays = self.search_count(domain)
               if nholidays >= holiday.holiday_status_id.no_per_service:
                    raise ValidationError(_('This leave type (%s) is eligble only %s times in period of service!!') % (holiday.holiday_status_id.name, holiday.holiday_status_id.no_per_service))
                
    
    @api.constrains('holiday_status_id', 'state')
    def _check_leave_attachement(self):
        for holiday in self:            
            if not holiday.technical and \
               holiday.holiday_status_id and \
               holiday.holiday_status_id.need_attachment: 
               if holiday.state not in ['draft'] and holiday.doc_count <= 0:
                    raise ValidationError(_('This leave type need a document. Please upload the required document to attachment!')) 
                
                
    @api.model
    def create(self, vals):
        holiday = super(HrHolidays, self).create(vals)
        employee_ids = []
        if vals.get('employee_id'):
            employee_ids.append(vals.get('employee_id'))
            coach = holiday.employee_id.coach_id
            manager = holiday.employee_id.parent_id
            if (coach):
                employee_ids.append(coach.id)
            if (manager):
                employee_ids.append(manager.id)
        if employee_ids:
            holiday.rec_add_followers(employee_ids=employee_ids,
                                         extend_groups=['hr.group_hr_user', 'hr.group_hr_manager'])
        return holiday
    
    @api.model
    def _needaction_domain_get(self):
        return ['|',
                '|',
                '|',
                '|',
                '|',
                '&', ('is_an_employee','=', True), ('state', 'in', ['draft', 'clarify']),
                '&', ('is_a_coach','=', True), ('state', '=', 'confirm'),
                '&', ('is_a_manager','=', True), ('state', '=', 'verify'),
                '&', ('is_a_hr_manager','=', True), ('state', '=', 'validate1'),
                '&',  '&', ('is_an_employee','=', True), ('state', '=', 'validate'), ('rec_msg_read', '=', True),
                '&',  '&', ('is_an_employee','=', True), ('state', '=', 'refuse'), ('rec_msg_read', '=', True)] 
    
    #~ @api.multi
    #~ def name_get(self):
        #~ res = []
        #~ for leave in self:
            #~ half_day = ''
            #~ if leave.half_day:
                #~ half_day = 'Half Day '
            #~ res.append((leave.id, _("%s on %s%s : %.2f day(s)") % (leave.employee_id.name or leave.category_id.name, half_day, leave.holiday_status_id.name, leave.number_of_days)))
        #~ return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        res = super(HrHolidays, self)._onchange_employee_id()
        if not isinstance(res, dict):
            res = {}
        domain = {}
        res_domain = {}
        if res.get('domain', False):
            res_domain = res['domain']                    
        self.contract_id = self.employee_id.contract_id
        hr_holiday_status = self.contract_id.hr_holiday_status_ids
        if self.holiday_status_id not in hr_holiday_status:
            self.holiday_status_id = False
        domain['holiday_status_id'] = [('id', 'in', hr_holiday_status.ids)]
        domain.update(res_domain)
        res['domain'] = domain 
        return res
    
    
    def _check_state_access_right(self, vals):
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'verify', 'validate1', 'clarify', 'cancel'] and not self.env['res.users'].has_group('cw_hr_extended.group_emp_coach'):
            return False
        return True
    
    @api.multi
    def action_verify(self):
        self.write({'state':'verify'})
        return True
    
    

    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('hr.group_emp_manager'):
            raise UserError(_('Only an Employee Manager, HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['verify']:
                raise UserError(_('Leave request must be verified in order to approve it.'))

            if holiday.double_validation:
                return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
            else:
                holiday.action_validate()

    #~ @api.multi
    #~ def action_validate(self):
        #~ for holiday in self:
            #~ if not holiday.double_validation:
                #~ holiday.write({'state':'confirm'})
            #~ if holiday.type == 'add' and not holiday.auto_allocated and (not holiday.date_from or not holiday.date_to):
                #~ date_today = datetime.now()                
                #~ date_today = date_today.replace(hour=00, minute=00, second=00)
                #~ date_from = False
                #~ if holiday.holiday_status_id.type == 'annual':
                    #~ current_year_anniversary_date = holiday.employee_id.current_year_anniversary_date                    
                    #~ current_year_anniversary_date = datetime.strptime(current_year_anniversary_date, DEFAULT_SERVER_DATE_FORMAT)
                    #~ date_from = current_year_anniversary_date
                    #~ if current_year_anniversary_date > date_today:
                        #~ last_year_anniversary_date = current_year_anniversary_date + relativedelta(years=-1)
                        #~ date_from = last_year_anniversary_date
                #~ else:
                    #~ company_id = holiday.employee_id.company_id             
                    #~ curr_year_company_start_date = company_id.curr_year_company_start_date
                    #~ if curr_year_company_start_date:
                        #~ curr_year_company_start_date = datetime.strptime(curr_year_company_start_date, DEFAULT_SERVER_DATE_FORMAT)
                        #~ date_from = curr_year_company_start_date                        
                        #~ if curr_year_company_start_date > date_today:
                            #~ last_year_company_date = curr_year_company_start_date + relativedelta(years=-1)
                            #~ date_from = last_year_company_date
                #~ if date_from:                        
                    #~ date_to = date_from + timedelta(days=364)
                    #~ date_from = date_from.replace(hour=00, minute=00, second=00)
                    #~ date_to = date_to.replace(hour=19, minute=59, second=59)
                    #~ date_from = date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)  
                    #~ date_to = date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    #~ if not holiday.date_from:
                        #~ holiday.date_from = date_from
                    #~ if not holiday.date_to:
                        #~ holiday.date_to = date_to
        #~ res = super(HrHolidays, self).action_validate()
        #~ return res

   

    @api.multi
    def action_refuse(self):
        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'verify', 'validate', 'validate1']:
                raise UserError(_('Leave request must be confirmed, verified or validated in order to refuse it.'))

            if holiday.state == 'validate1':
                holiday.write({'state': 'refuse', 'manager_id': manager.id})
            else:
                holiday.write({'state': 'refuse', 'manager_id2': manager.id})
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        self._remove_resource_leave()
        return True

    @api.multi
    def action_draft(self):
        res = super(HrHolidays, self).action_draft()
        for holiday in self:
            if not holiday.auto_allocated:
                holiday.write({'date_from': None, 'date_to': None})
        return res    
                
    #~ @api.onchange('date_from')
    #~ def _onchange_date_from(self):
        #~ if self.date_from:
            #~ date_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
            #~ date_from = datetime.combine(date_from, dt_time.min)
            #~ user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'          
            #~ date_from = to_tz(date_from, user_tz)
            #~ self.date_from = date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #~ res = super(HrHolidays, self)._onchange_date_from()
        #~ if self.half_day:
            #~ self.number_of_days = self.number_of_days / 2
        #~ return res

    #~ @api.onchange('date_to')
    #~ def _onchange_date_to(self): 
        #~ if self.date_to:
            #~ date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
            #~ date_to = datetime.combine(date_to, dt_time.max)
            #~ date_to = to_naive_utc(date_to, self.env.user) 
            #~ self.date_to = date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #~ res = super(HrHolidays, self)._onchange_date_to()
        #~ if self.half_day:
            #~ self.number_of_days_temp = self.number_of_days_temp / 2
        #~ return res

    #~ @api.onchange('half_day')
    #~ def _onchange_half_day(self):
        #~ if (self.date_to and self.date_from) and (self.date_from <= self.date_to):
            #~ self.number_of_days_temp = self._recompute_number_of_days()
            #~ if self.half_day:
                #~ self.number_of_days_temp = self.number_of_days_temp / 2                

    @api.multi
    def compute_custom_number_of_days(self, date_from, date_to):
        self.ensure_one()        
        #date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        #date_from = datetime.combine(date_from, dt_time.min)
        #user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'          
        #date_from = to_tz(date_from, user_tz)
        #date_from = date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)        
        
        #date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
        #date_to = datetime.combine(date_to, dt_time.max)
        #date_to = to_naive_utc(date_to, self.env.user) 
        #date_to = date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)      
        
        employee_id = self.employee_id.id
        if not date_from or not date_to:
            return 0
        days = self._get_number_of_days(date_from, date_to, None)
        if date_to == date_from:
            days = 1

        status_id = self.holiday_status_id.id or self.env.context.get('holiday_status_id', False)
        if employee_id and date_from and date_to and status_id:
            employee = self.env['hr.employee'].browse(employee_id)
            status = self.env['hr.leave.type'].browse(status_id)
            date_from = fields.Date.from_string(date_from)
            date_to = fields.Date.from_string(date_to)
            date_dt = date_from
            while date_dt <= date_to:
                # if public holiday or rest day let us skip
                if not employee.work_scheduled_on_day(
                        date_dt,
                        status.exclude_public_holidays,
                        status.exclude_rest_days,
                ):
                    days -= 1
                date_dt += relativedelta(days=1)        
        if self.request_unit_half:
            days = days / 2
        return days
                
    @api.multi
    def recompute_given_fields(self):
        #ids = [holiday.id for holiday in self] 
        #holiday_domain = [('id', 'in', ids)] 
        #holidays = self.search(holiday_domain) 
        self.env.add_todo(self._fields['number_of_days'], self)
        self.recompute()
        return True
    
    @api.model
    def calculate_prorated_given_date(self, from_date, given_date, contract):
        given_date = datetime.strptime(given_date, DEFAULT_SERVER_DATETIME_FORMAT)
        from_date = datetime.strptime(from_date, DEFAULT_SERVER_DATETIME_FORMAT)
        annual_days = contract.annual_days
        #To Do : Is annual days is always correct?(probably -yes) and how we got 365.0 - difference between from and to date -- see prorated_days in hr.holidays
        daily_allocate = float(annual_days / 365.0)
        prorate_day_diff = given_date - from_date
        total_prorate_days = float(prorate_day_diff.days)
        prorated_days = float(daily_allocate * total_prorate_days)
        return prorated_days
                
        
    
    
    
    
