# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class Contact(models.Model):
    _inherit = 'res.partner'

    is_group = fields.Boolean('Is Group')
    group_code = fields.Char('Group Code')
    company_code = fields.Char('Company Code')
    company_group_id = fields.Many2one(
        'res.partner',
        'Company group',
        domain=[('is_group', '=', True)]
    )
    child_company_ids = fields.One2many('res.partner','company_group_id',string='Child Companies')

    def _commercial_fields(self):
        return super(Contact, self)._commercial_fields() + ['company_group_id']
