# -*- coding: utf-8 -*-

from datetime import date
from openerp import fields, models, api, _
from openerp.exceptions import Warning as UserError


class HrPublicHolidays(models.Model):
    _inherit = 'hr.holidays.public'

    @api.multi
    def recalc_holidays(self):
        for pub_hol in self:
            for pub_line in pub_hol.line_ids:
                pub_line_date = pub_line.date
                existing = self.env['hr.leave'].search([
                        ('type', '=', 'remove'),
                        ('holiday_status_id.exclude_public_holidays', '=', True),
                        '|',
                        ('date_from', '>=', pub_line_date),
                        ('date_to', '<=', pub_line_date)
                    ])
                for ex_hol in existing:
                    if (ex_hol.date_to and ex_hol.date_from) and (ex_hol.date_from <= ex_hol.date_to):
                        number_of_days = ex_hol._recompute_number_of_days()
                        if ex_hol.number_of_days != number_of_days:
                            # self.env.invalidate_all()
                            self.env.cr.execute(""" UPDATE hr_leave SET number_of_days = %s WHERE id = %s""" % (number_of_days, ex_hol.id))
    
