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



class HrHolidaysAllocation(models.Model):
    _name = "hr.leave.allocation"
    _inherit = ['hr.leave.allocation', 'mail.thread', 'ir.model.role','mail.activity.mixin', 'common.clarify']

    
    
    def _default_contract(self):
        employee_id = self.env.context.get('default_employee_id', False)
        contract_id = self.env['hr.contract']
        if employee_id:
            employee = self.env['hr.employee'].search([('id', '=', employee_id)], limit=1)
            contract_id =  employee and employee.contract_id or self.env['hr.contract']
        return contract_id

    @api.multi
    def _compute_prorated_days(self):
        for holiday in self:
            number_of_days = holiday.number_of_days
            prorated_days = number_of_days
            if  holiday.auto_allocated and \
                holiday.holiday_status_id and \
                holiday.holiday_status_id.prorated and number_of_days > 0.0:                                
                date_today = datetime.now()                
                date_today = date_today.replace(hour=00, minute=00, second=00)
                date_from = holiday.date_from
                date_to = holiday.date_to
                if date_from and date_to:
                    date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
                    date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
                    if date_today >= date_to:
                        prorated_days = number_of_days
                    elif date_today < date_from:
                        prorated_days = 0.0                        
                    elif date_from <= date_today <= date_to:
                        total_day_diff = date_to - date_from
                        total_days = float(total_day_diff.days)
                        daily_allocate = float(number_of_days / total_days)
                        prorate_day_diff = date_today - date_from
                        total_prorate_days = float(prorate_day_diff.days)
                        prorated_days = float(daily_allocate * total_prorate_days)
            holiday.prorated_days = prorated_days      
    
    @api.multi
    @api.depends('number_of_days', 'auto_allocated', 'holiday_status_id.prorated')
    def _compute_number_of_days_display(self):        
        super(HrHolidaysAllocation, self)._compute_number_of_days_display()
        for holiday in self:
            if holiday.auto_allocated and \
               holiday.holiday_status_id and \
               holiday.holiday_status_id.prorated and holiday.number_of_days > 0.0:              
               holiday.no_of_days = holiday.prorated_days
    

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
            holi_attachments = attachment.search([('res_model', '=', 'hr.holidays'), ('res_id', '=', holi.id)], count=True)
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
    auto_allocated = fields.Boolean(string="Auto Allocated", default=False, copy=False)
    doc_count = fields.Integer(compute='_get_attached_docs', string="Number of documents attached")
    waiting_list_no = fields.Integer('Waiting List Number', compute='_compute_waiting_list_no', store=True)
    prorated_days = fields.Float('Prorated Days')
    no_of_days = fields.Float(compute='_compute_number_of_days_display') 
    
    
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
        holiday = super(HrHolidaysAllocation, self).create(vals)
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

    
    @api.onchange('employee_id')
    def _onchange_employee(self):
        res = super(HrHolidaysAllocation, self)._onchange_employee()
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
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('cw_hr_extended.group_emp_manager'):
            raise UserError(_('Only an Employee Manager, HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['verify']:
                raise UserError(_('Leave request must be verified in order to approve it.'))

            if holiday.double_validation:
                return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
            else:
                holiday.action_validate()



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
            #~ if holiday.meeting_id:
                #~ holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        #~ self._remove_resource_leave()
        return True

    @api.multi
    def action_draft(self):
        res = super(HrHolidaysAllocation, self).action_draft()
        for holiday in self:
            if not holiday.auto_allocated:
                holiday.write({'date_from': None, 'date_to': None})
        return res    

    @api.multi
    def recompute_given_fields(self):
        #ids = [holiday.id for holiday in self] 
        #holiday_domain = [('id', 'in', ids)] 
        #holidays = self.search(holiday_domain) 
        self.env.add_todo(self._fields['no_of_days'], self)
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
