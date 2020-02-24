# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountFiscalYearCloseState(models.TransientModel):

    _name = "account.fiscalyear.close.state"
    _description = "Fiscalyear Close state"

    company_id = fields.Many2one(
        'res.company', string='Company')
    fy_id = fields.Many2one('account.fiscalyear', 'Fiscal Year to Close',
                            help="Select a fiscal year to close")

    @api.multi
    def data_save(self):
        for data in self:
            fy_id = data.fy_id
            if not fy_id:
                raise ValidationError(_("Please select fiscal year.!!"))
            self._cr.execute(
                "UPDATE account_fiscalyear SET state='done' WHERE id = %s"
                % (fy_id.id))
            self._cr.execute("UPDATE account_period SET state='done' WHERE"
                             "fiscalyear_id=%s and company_id=%s" %
                             (fy_id.id, data.company_id.id))
            data.company_id.period_lock_date =\
                data.company_id.fiscalyear_lock_date = fy_id.date_stop
            self.invalidate_cache()
            return {'type': 'ir.actions.act_window_close'}
