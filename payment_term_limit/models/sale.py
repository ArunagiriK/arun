from odoo import models,fields,api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        due_invoices = self.env['account.invoice'].search([('state', '=', 'open'),
                                                           ('date_due', '<', fields.Date.today()),
                                                           ('partner_id', '=', self.partner_id.id)])
        if due_invoices and self.partner_id.is_restrict_payment_term:
            raise UserError ('Can not confirm due to Due invoices')
        return super(SaleOrder, self).action_confirm()