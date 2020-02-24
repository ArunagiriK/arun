from datetime import date, datetime
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TermPeriodic(models.Model):
    _name = 'partner.term.periodic'

    invoice_from_date = fields.Date(string='From Date')
    invoice_to_date = fields.Date(string='To Date')
    execution_date = fields.Date(string='Next Execution Date')
    partner_execution_id = fields.Many2one('res.partner',string='Partner Terms')
    terms_id = fields.Many2one('partner.term.calculation')
    term_calculation_type = fields.Selection([
        ('on_invoice', 'On Invoice'),
        ('automatic', 'Automatic'),
           ])
    frequency = fields.Selection([
        ('only_once', 'Only Once'),
        ('periodic', 'Periodic'),
    ])


    @api.onchange('terms_id')
    def PartnerTermLine(self):
        self.term_calculation_type = self.terms_id.term_calculation_type
        self.frequency = self.terms_id.frequency






