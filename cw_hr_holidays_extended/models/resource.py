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

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"
    
    @api.multi
    def is_restday(self, selected_date):
        if isinstance(selected_date, str):
            selected_date = fields.Date.from_string(selected_date)
        hours = self.get_working_hours_of_date(datetime.combine(selected_date, time.min))
        if hours:
            return True
        else:
            return False    
