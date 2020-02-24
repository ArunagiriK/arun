# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class FiscalYearPeriodClose(models.TransientModel):

    _name = "fiscalyear.period.close"
    _description = "Fiscalyear Period Close"

    company_id = fields.Many2one('res.company', string='Company')
    fy_id = fields.Many2one('account.fiscalyear',
                            'Fiscal Year', help="Select a fiscal year")
    period_id = fields.Many2one('account.period', 'Period to Close')

    @api.onchange('company_id', 'fy_id')
    def onchange_company_fiscalyear(self):
        for rec in self:
            args = {'period_id': [
                ('company_id', '=', rec.company_id.id),
                ('state', '=', 'draft')]}
            if rec.fy_id:
                args['period_id'] += [('fiscalyear_id', '=', rec.fy_id.id)]
        return {'domain': args}

    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            rec.fy_id = False
            rec.period_id = False

    @api.onchange('fy_id')
    def onchange_fy_id(self):
        for rec in self:
            rec.period_id = False

    @api.multi
    def data_save(self):
        period_obj = self.env['account.period']
        for data in self:
            if not data.period_id:
                raise ValidationError(_("Please select fiscal year period.!!"))
            period = data.period_id
            fy_id = period.fiscalyear_id
            period_recs = period_obj.search(
                [('date_stop', '<', period.date_stop),
                 ('state', '=', 'draft'),
                 ('fiscalyear_id', '=', fy_id.id)], limit=1)
            self._cr.execute('UPDATE account_period SET state = %s '
                             'WHERE fiscalyear_id = %s and id = %s',
                             ('done', fy_id.id, period.id))
            if not period_recs:
                data.company_id.period_lock_date =\
                    data.company_id.fiscalyear_lock_date = period.date_stop
            else:
                date_stop = datetime.strptime(
                    period_recs.date_start, DEFAULT_SERVER_DATE_FORMAT)
                lock_date = (date_stop + relativedelta(days=-1)).\
                    strftime('%Y-%m-%d')
                data.company_id.period_lock_date =\
                    data.company_id.fiscalyear_lock_date = lock_date
            self.invalidate_cache()
            return {'type': 'ir.actions.act_window_close'}
