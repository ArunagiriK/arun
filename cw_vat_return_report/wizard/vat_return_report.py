# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Codeware LLC
##############################################################################

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class AccountVatReturnReportWizard(models.TransientModel):
    _name = "account.vat.return.report.wizard"
    _description = "Account Vat Return Report"

    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env.user.company_id)
    from_date = fields.Date('From', default=lambda *a: time.strftime('%Y-%m-01'))
    to_date = fields.Date('To', default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    date_range_id = fields.Many2one('date.range', 'Date range', required=False)
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
    ], 'Target Moves', required=True, default='posted')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.from_date = self.date_range_id.date_start
            self.to_date = self.date_range_id.date_end
        else:
            self.from_date = time.strftime('%Y-%m-01')
            self.to_date = str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10]

    #@api.multi
    #def export_account_vat_return_report(self):        
    #    self.ensure_one()
    #    return self.env.ref('cw_vat_return_report.account_vat_return_xlsx').report_action(self)