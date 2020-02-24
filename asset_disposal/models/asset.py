from odoo import _, api, fields, models

from odoo.exceptions import UserError
import math
from datetime import datetime
import calendar
from datetime import datetime, timedelta

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    
    @api.multi
    @api.depends('depreciation_line_ids.move_id','disposed_move_id')
    def _entry_count(self):
        for asset in self:
            res = self.env['account.asset.depreciation.line'].search_count([('asset_id', '=', asset.id), ('move_id', '!=', False)])
            if asset.disposed_move_id:
                res = res + 1
            asset.entry_count = res or 0

    entry_count = fields.Integer(compute='_entry_count', string='# Asset Entries')
    disposed_move_id = fields.Many2one('account.move',string='Disposed Move', copy=False)
    date_wizard = fields.Date('Date')
    disposal_type = fields.Selection([('sale', 'Sale'), ('writeoff', 'Write-Off')], 'Disposal Type')
    disposal_partner_id = fields.Many2one('res.partner', 'Partner')
    sale_amount =  fields.Float(string="Sale Amount")
    disposal_residual_amount = fields.Float(string="Residual Amount")
    cus_invoice_id = fields.Many2one('account.invoice', string="Customer Invoice Ref")
    
    @api.multi
    def open_entries(self):
        move_ids = []
        for asset in self:
            for depreciation_line in asset.depreciation_line_ids:
                if depreciation_line.move_id:
                    move_ids.append(depreciation_line.move_id.id)
            if asset.disposed_move_id:
                move_ids.append(asset.disposed_move_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }

class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'
    
    disposal_gain_account_id = fields.Many2one('account.account', string="Disposal Gain Account")
    disposal_loss_account_id = fields.Many2one('account.account', string="Disposal Loss Account")
    
    
            


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: