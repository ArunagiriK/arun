from datetime import date, datetime
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_terms_ids = fields.One2many('partner.term.periodic','partner_execution_id', string="Partner Terms")
    rebate_perc_amount = fields.Float('Rebate Percentage Amount')
    rebate_fixed_amount = fields.Float('Rebate Fixed Amount')
    @api.model
    def create(self, vals):
        if vals.get('partner_terms_ids'):
            if not vals.get('company_group_id'):
                child_partners = self.env['res.partner'].search([('company_group_id', '=', vals.get('id'))])
                for partner in child_partners:
                    partner.write({'partner_terms_ids': vals.get('partner_terms_ids')})
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('partner_terms_ids'):
            if not vals.get('company_group_id') and not self.company_group_id:
                child_partners = self.env['res.partner'].search([('company_group_id', '=', self.id)])
                for partner in child_partners:
                    partner.write({'partner_terms_ids': vals.get('partner_terms_ids')})
        return super(ResPartner, self).write(vals)



