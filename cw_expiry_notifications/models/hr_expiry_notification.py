# -*- coding: utf-8 -*-

import logging
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class HrExpiryNotification(models.Model):
    _name = "hr.expiry.notification"
    #_inherit = ['mail.thread', 'ir.needaction_mixin', 'ir.model.role']
    _order = "id desc"
    #_employee_id = 'employee_id' 

    @api.multi
    @api.depends('employee_id')
    def _get_emp_data(self):
        for expiry_notify in self:
            employee = expiry_notify.employee_id
            expiry_notify.update({
                'department_id': employee.department_id,
                'job_id': employee.job_id,
                'contract_id': employee.contract_id,
                'employee_code': employee.identification_id,
                'emirate_id': employee.emirate_id,
                'passport_id': employee.passport_id,
                'visa_no': employee.visa_no,
                'healthcard_id': employee.healthcard_id,
                'fire_safety_id': employee.fire_safety_id,
                'hazmat_id': employee.hazmat_id,
            })

    @api.multi
    @api.depends('expire_date')
    def _get_date_data(self):
        for expiry_notify in self:
            days_left = 0
            if expiry_notify.expire_date:
                expire_date = datetime.strptime(expiry_notify.expire_date, DEFAULT_SERVER_DATE_FORMAT)
                today = fields.Datetime.from_string(fields.Datetime.now())
                diff_time = (expire_date - today).days
                days_left = diff_time > 0 and diff_time or 0
            expiry_notify.update({
                'days_left': days_left,
            })

    @api.model
    @api.multi
    def _search_days_left(self, operator, value):     
        assert operator in ('=', '!=', '<', '>', '<=', '>='), 'Invalid domain operator'
        assert isinstance(value, (int, float, str)), 'Invalid value'
        today = fields.Datetime.from_string(fields.Datetime.now())
        value = int(value)        
        search_value = today + timedelta(days=value)
        search_value = fields.Date.to_string(search_value)
        records = self.search([('expire_date', operator, search_value)])
        return [('id', 'in', records.ids)] 
    
    name = fields.Char(string='Name', required=True, readonly=True, copy=False)
    date = fields.Date(string='Created Date', required=True, readonly=True, copy=False, default=fields.Date.today)
    expire_date = fields.Date(string='Expiry Date', readonly=True, required=True, copy=False)
    note = fields.Text(string='Message', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, required=True, copy=False)
    dependent_id = fields.Many2one('hr.dependents.line', 'Dependent ID')
    #department_id = fields.Many2one("hr.department", related='employee_id.department_id', string="Department", readonly=True, copy=False, store=True)
    #employee_code = fields.Char(string='Code', related='employee_id.identification_id', readonly=True, copy=False, store=True)
    department_id = fields.Many2one("hr.department", string='Department', compute="_get_emp_data", readonly=True, copy=False, store=True)
    job_id = fields.Many2one("hr.job", string='Job Position', compute="_get_emp_data", readonly=True, copy=False, store=True)
    contract_id = fields.Many2one("hr.contract", string='Current Contract', compute="_get_emp_data", readonly=True, copy=False, store=True)
    employee_code = fields.Char(string='Code', compute="_get_emp_data", readonly=True, copy=False, store=True)
    emirate_id = fields.Char(string='Emirate ID No', compute="_get_emp_data", readonly=True, copy=False, store=True)
    visa_no = fields.Char(string='Visa No', compute="_get_emp_data", readonly=True, copy=False, store=True)
    passport_id = fields.Char(string='Passport No', compute="_get_emp_data", readonly=True, copy=False, store=True)
    healthcard_id = fields.Char(string='Health Card No', compute="_get_emp_data", readonly=True, copy=False, store=True)
    fire_safety_id = fields.Char(string='Fire & Safety Certificate No', compute="_get_emp_data", readonly=True, copy=False, store=True)
    hazmat_id = fields.Char(string='HAZMAT Certificate No', compute="_get_emp_data", readonly=True, copy=False, store=True)
    other_id = fields.Char(string='Certificate No', readonly=True, copy=False)
    type = fields.Selection([('emirate', 'Emirate'), 
                             ('passport', 'Passport'), 
                             ('visa', 'Visa'),
                             ('health', 'Health'), 
                             ('fire_safety','Fire & Safety'), 
                             ('hazmat','Hazmat'), 
                             ('other','Other')],
                            string='Type', readonly=True, required=True, copy=False, default='other')
    days_left = fields.Integer(string='Days Remaining', compute="_get_date_data", search='_search_days_left', readonly=True, copy=False)
    active = fields.Boolean(string='Active', default=True, readonly=True, copy=False)
    type_of_document = fields.Char(string='Type of Document', readonly=True, copy=False)
    employee_document_id = fields.Many2one('hr.employee.document', string='Employee Document', readonly=True, copy=False)
    
    @api.multi
    def action_solve(self):
        type = self.env.context.get('type', False)
        domain = []
        ctx = self._context.copy()
        if type:
            domain.append(('type', '=', type))
        self.write({'active': False})        
        notify_ids = self.search(domain).mapped('id')
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.expiry.notification',
            'domain': [('id', 'in', notify_ids)],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'nodestroy': False,
            'context': ctx,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: