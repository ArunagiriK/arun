import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    refund_invoice_id = fields.Many2one(related='invoice_id.refund_invoice_id',
                                        string='Invoice for which this invoice is the refund')