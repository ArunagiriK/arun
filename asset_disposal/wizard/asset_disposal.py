from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AssetDisposal(models.TransientModel):
    _name = 'asset.disposal'
    _description = 'Asset Disposal'

    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    date = fields.Date('Date', required=True)
    type = fields.Selection([('sale', 'Sale'), ('writeoff', 'Write-Off')], 'Disposal Type', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    sale_amount = fields.Float(string="Sale Amount")
    residual_amount = fields.Float(string="Residual Amount")

    @api.multi
    def action_sell(self):
        aml_obj = self.env['account.move.line']
        move_pool = self.env['account.move']
        invoice_pool = self.env['account.invoice']
        for rec in self:
            cus_invoice_id = False
            if rec.asset_id:
                mov_vals = {
                    'ref': rec.asset_id.name or ' ',
                    'journal_id': rec.asset_id.category_id.journal_id.id or False,
                    'date': rec.date or False,
                }
                move = move_pool.create(mov_vals)
                journal_id = rec.asset_id.category_id.journal_id.id
                if rec.type == 'writeoff':
                    asset_amount = (rec.asset_id.actual_value - rec.asset_id.value_residual)
                    debit_asset_amount, credit, amount_currency, currency_id = aml_obj._compute_amount_fields(
                        asset_amount, rec.asset_id.currency_id, rec.asset_id.company_id.currency_id)
                    account_depreciation_id = rec.asset_id.category_id.account_depreciation_id.id or False
                    disposal_loss_account_id = rec.asset_id.category_id.disposal_loss_account_id.id or False
                    account_asset_id = rec.asset_id.category_id.account_asset_id.id or False
                    if not account_depreciation_id or not disposal_loss_account_id or not account_asset_id:
                        raise UserError(_("Please configure your Accounts or contact your administrator!!"))
                    name = rec.asset_id.related_product_id.name
                    move_lines = []
                    debit_move_vals = {
                        'name': name,
                        'invoice_id': False,
                        'journal_id': journal_id,
                        'currency_id': currency_id or False,
                        'credit': 0.00,
                        'debit': debit_asset_amount,
                        'amount_currency': amount_currency,
                        'partner_id': rec.asset_id.partner_id and rec.asset_id.partner_id.id or False,
                        'move_id': move.id,
                        'account_id': account_depreciation_id
                    }
                    move_lines.append((0, 0, debit_move_vals))
                    debit_residual_value_amount, credit, amount_currency, currency_id = aml_obj._compute_amount_fields(
                        rec.asset_id.value_residual, rec.asset_id.currency_id, rec.asset_id.company_id.currency_id)
                    debit_move_vals = {
                        'name': name,
                        'invoice_id': False,
                        'journal_id': journal_id,
                        'currency_id': currency_id or False,
                        'credit': 0.00,
                        'debit': debit_residual_value_amount,
                        'amount_currency': amount_currency,
                        'partner_id': rec.asset_id.partner_id and rec.asset_id.partner_id.id or False,
                        'move_id': move.id,
                        'account_id': disposal_loss_account_id
                    }
                    move_lines.append((0, 0, debit_move_vals))
                    debit_amount, credit_asset_amount, amount_currency, currency_id = aml_obj._compute_amount_fields(
                        (rec.asset_id.actual_value) * -1, rec.asset_id.currency_id, rec.asset_id.company_id.currency_id)
                    credit_move_vals = {
                        'name': name,
                        'invoice_id': False,
                        'journal_id': journal_id,
                        'currency_id': currency_id or False,
                        'credit': credit_asset_amount,
                        'debit': 0.00,
                        'amount_currency': amount_currency * -1.00,
                        'partner_id': rec.asset_id.partner_id and rec.asset_id.partner_id.id or False,
                        'move_id': move.id,
                        'account_id': account_asset_id
                    }
                    move_lines.append((0, 0, credit_move_vals))
                    move.write({'line_ids': move_lines, 'ref': rec.asset_id.name + " Disposal"})
                else:
                    # Invoice Creation
                    line_list = []
                    product_account_id = False
                    sale_amount = rec.sale_amount
                    residual_value = rec.residual_amount

                    if sale_amount >= residual_value:
                        disposal_account_id = rec.asset_id.category_id.disposal_gain_account_id.id or False
                    else:
                        disposal_account_id = rec.asset_id.category_id.disposal_loss_account_id.id or False
                    if rec.asset_id.related_product_id:
                        name = rec.asset_id.related_product_id.name_get()[0][1]
                    else:
                        name = ''
                    line_dict = {
                        'product_id': rec.asset_id.related_product_id.id or False,
                        'name': name,
                        'account_id': disposal_account_id,
                        'price_unit': sale_amount or 0.0
                    }
                    line_list.append((0, 0, line_dict))
                    invoice_dict = {
                        'partner_id': rec.partner_id.id or False,
                        'date_invoice': rec.date or '',
                        'type': 'out_invoice',
                        'state': 'draft',
                        'origin': rec.asset_id.name,
                        'invoice_line_ids': line_list
                    }
                    cus_invoice_id = invoice_pool.create(invoice_dict)
                    # Journal Creation
                    asset_amount = (rec.asset_id.actual_value - rec.asset_id.value_residual)
                    debit_asset_amount, credit, amount_currency, currency_id = aml_obj._compute_amount_fields(
                        asset_amount, rec.asset_id.currency_id, rec.asset_id.company_id.currency_id)
                    account_depreciation_id = rec.asset_id.category_id.account_depreciation_id.id or False
                    account_asset_id = rec.asset_id.category_id.account_asset_id.id or False
                    if not account_depreciation_id or not disposal_account_id or not account_asset_id:
                        raise UserError(_("Please configure your Accounts or contact your administrator!!"))
                    name = rec.asset_id.related_product_id.name
                    move_lines = []
                    debit_move_vals = {
                        'name': name,
                        'invoice_id': False,
                        'journal_id': journal_id,
                        'currency_id': currency_id or False,
                        'credit': 0.00,
                        'debit': debit_asset_amount,
                        'amount_currency': amount_currency,
                        'partner_id': rec.asset_id.partner_id and rec.asset_id.partner_id.id or False,
                        'move_id': move.id,
                        'account_id': account_depreciation_id
                    }
                    move_lines.append((0, 0, debit_move_vals))
                    debit_residual_value_amount, credit, amount_currency, currency_id = aml_obj._compute_amount_fields(
                        rec.asset_id.value_residual, rec.asset_id.currency_id, rec.asset_id.company_id.currency_id)
                    debit_move_vals = {
                        'name': name,
                        'invoice_id': False,
                        'journal_id': journal_id,
                        'currency_id': currency_id or False,
                        'credit': 0.00,
                        'debit': debit_residual_value_amount,
                        'amount_currency': amount_currency,
                        'partner_id': rec.asset_id.partner_id and rec.asset_id.partner_id.id or False,
                        'move_id': move.id,
                        'account_id': disposal_account_id
                    }
                    move_lines.append((0, 0, debit_move_vals))
                    debit_amount, credit_asset_amount, amount_currency, currency_id = aml_obj._compute_amount_fields(
                        (rec.asset_id.actual_value) * -1, rec.asset_id.currency_id, rec.asset_id.company_id.currency_id)
                    credit_move_vals = {
                        'name': name,
                        'invoice_id': False,
                        'journal_id': journal_id,
                        'currency_id': currency_id or False,
                        'credit': credit_asset_amount,
                        'debit': 0.00,
                        'amount_currency': amount_currency * -1.00,
                        'partner_id': rec.asset_id.partner_id and rec.asset_id.partner_id.id or False,
                        'move_id': move.id,
                        'account_id': account_asset_id
                    }
                    move_lines.append((0, 0, credit_move_vals))
                    move.write({'line_ids': move_lines, 'ref': rec.asset_id.name + " Sell"})

                rec.asset_id.disposed_move_id = move.id
                rec.asset_id.date_wizard = rec.date
                rec.asset_id.disposal_type = rec.type
                rec.asset_id.disposal_partner_id = rec.partner_id.id
                rec.asset_id.sale_amount = rec.sale_amount
                rec.asset_id.disposal_residual_amount = rec.residual_amount
                if cus_invoice_id:
                    rec.asset_id.cus_invoice_id = cus_invoice_id.id or False
                rec.asset_id.state = 'close'
                if rec.asset_id.depreciation_line_ids:
                    move_ids = []
                    for depreciation_line in rec.asset_id.depreciation_line_ids:
                        if not depreciation_line.move_id:
                            depreciation_line.unlink()

        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', move.id)],
        }
