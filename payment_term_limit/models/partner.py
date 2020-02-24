from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_restrict_payment_term = fields.Boolean('Enable Payment Terms Restriction')
