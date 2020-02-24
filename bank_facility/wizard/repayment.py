# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)



class AccountRepayment(models.TransientModel):
    _name = 'account.repayment'
    _description = 'Amount Repayment'

    name = fields.Char('Name')
    date =  fields.Date('Date',required=True)
    account_payable = fields.Many2one('account.account','Payable Account A/c' ,required=True)
    
    @api.multi
    def action_wizard_repayment(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            inv = self.env['account.payment'].browse(active_id)
            #~ days_after = (inv.payment_date + timedelta(days=90))
            #~ if self.date and self.date <= days_after:
                #~ raise ValidationError(_('The repayment date must be 90 after payment date.'))
            return inv.action_repayment(self.date, self.account_payable)
        return ''
    
    
