from odoo import api, models, fields, _
import calendar
from datetime import datetime, timedelta
from odoo.exceptions import Warning
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_compare, float_is_zero

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.one
    def asset_create(self):
        if self.asset_category_id:
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal_signed,
                'actual_value': self.price_subtotal_signed,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.company_currency_id.id,
                'date': self.invoice_id.date_invoice,
                'actual_date': self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
                'related_product_id': self.product_id.id or False,
            }
            changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
            vals.update(changed_vals['value'])
            asset = self.env['account.asset.asset'].create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()
        return True
       