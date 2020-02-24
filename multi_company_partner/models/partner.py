from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_ids = fields.Many2many(comodel_name='res.company', relation='partner__company_rel',
                                   column1='partner_id', column2='company_id', string='Companies')