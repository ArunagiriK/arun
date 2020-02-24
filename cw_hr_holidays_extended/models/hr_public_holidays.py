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
                existing = self.env['hr.holidays'].search([
                        ('type', '=', 'remove'),
                        ('holiday_status_id.exclude_public_holidays', '=', True),
                        '|',
                        ('date_from', '>=', pub_line_date),
                        ('date_to', '<=', pub_line_date)
                    ])
                for ex_hol in existing:
                    # old_number_of_days_temp = ex_hol.number_of_days_temp                 
                    if (ex_hol.date_to and ex_hol.date_from) and (ex_hol.date_from <= ex_hol.date_to):
                        number_of_days_temp = ex_hol._recompute_number_of_days()
                        if ex_hol.half_day:
                            number_of_days_temp = number_of_days_temp / 2                        
                        if ex_hol.number_of_days_temp != number_of_days_temp:
                            # ex_hol.with_context(overwrite=True).write({'number_of_days_temp':number_of_days_temp})
                            # self.env.invalidate_all()
                            self.env.cr.execute(""" UPDATE hr_holidays SET number_of_days_temp = %s WHERE id = %s""" % (number_of_days_temp, ex_hol.id))
    
