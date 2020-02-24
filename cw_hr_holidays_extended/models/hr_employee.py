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

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    @api.multi
    def _inverse_remaining_leaves(self):
        status_list = self.env['hr.leave.type'].search([('time_type', '=', 'leave'), ('type', '=', 'annual')])
        # Create leaves (adding remaining leaves) or raise (reducing remaining leaves)
        actual_remaining = self._get_remaining_leaves()
        for employee in self.filtered(lambda employee: employee.remaining_leaves):
            # check the status list. This is done here and not before the loop to avoid raising
            # exception on employee creation (since we are in a computed field).
            if len(status_list) != 1:
                raise UserError(_("The feature behind the field 'Remaining Legal Leaves' can only be used when there is only one "
                    "leave type with the option 'Allow to Override Limit' unchecked. (%s Found). "
                    "Otherwise, the update is ambiguous as we cannot decide on which leave type the update has to be done. "
                    "\n You may prefer to use the classic menus 'Leave Requests' and 'Allocation Requests' located in Leaves Application "
                    "to manage the leave days of the employees if the configuration does not allow to use this field.") % (len(status_list)))
            status = status_list[0] if status_list else None
            if not status:
                continue
            # if a status is found, then compute remaing leave for current employee
            difference = employee.remaining_leaves - float_round(actual_remaining.get(employee.id, 0), precision_digits=2)
            if difference > 0:
                leave = self.env['hr.leave.allocation'].create({
                    'name': _('Allocation for %s') % employee.name,
                    'employee_id': employee.id,
                    'holiday_status_id': status.id,
                    'holiday_type': 'employee',
                    'number_of_days': difference
                })
                leave.action_approve()
                if leave.holiday_status_id.double_validation:
                    leave.action_validate()
            elif difference < 0:
                raise UserError(_('You cannot reduce validated allocation requests'))
    
    
    remaining_leaves = fields.Float(inverse='_inverse_remaining_leaves', digits=(16, 2))
    
    current_leave_state = fields.Selection(selection=[
                            ('draft', 'To Submit'),
                            ('clarify', 'Under Clarify'),
                            ('cancel', 'Cancelled'),
                            ('confirm', 'Confirmed'),
                            ('refuse', 'Refused'),
                            ('verify', 'Verified'),
                            ('validate1', 'Validated'),
                            ('validate', 'Approved')
                            ])
    

    @api.multi
    def work_scheduled_on_day_X(self, date_dt, public_holiday=True, schedule=True):
        self.ensure_one()
        if public_holiday and self.env['hr.holidays.public'].is_public_holiday(
                date_dt, employee_id=self.id):
            return False
        elif schedule and self.contract_id and self.contract_id.resource_calendar_id and \
            self.contract_id.resource_calendar_id.is_restday(date_dt):
            return False
        elif schedule and (not self.contract_id or (
                self.contract_id and not self.contract_id.resource_calendar_id)):
            return date_dt.weekday() not in (4, 5)
        return True
    

class HrDepartment(models.Model):
    _inherit = "hr.department"
    
    overlapping_leaves = fields.Integer('Overlapping Leaves')


    
