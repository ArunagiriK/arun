# -*- coding: utf-8 -*-

from datetime import timedelta, date, datetime, time as dt_time, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, rrule, MO, TU, WE, TH, FR, SA, SU

from odoo import api, fields, models, _
from odoo.addons.hr_holidays.report.holidays_summary_report import HrHolidaySummaryReport
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class HrHolidaySummaryReportExtended(models.AbstractModel):
    _name = 'report.hr_holidays.report_holidayssummary'
    _inherit = 'report.hr_holidays.report_holidayssummary'

    def _get_header_info(self, start_date, holiday_type):
        st_date = fields.Date.from_string(start_date)
        res = super(HrHolidaySummaryReportExtended, self)._get_header_info(start_date, holiday_type)
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])        
        format_date = lang and lang.date_format or '%d-%m-%Y'        
        res.update({
            'start_date': st_date.strftime(format_date),
            'end_date': (st_date + relativedelta(days=59)).strftime(format_date),
        })
        return res
