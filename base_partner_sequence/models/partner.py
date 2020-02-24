# Copyright 2004-2009 Tiny SPRL (<http://tiny.be>).
# Copyright 2013 initOS GmbH & Co. KG (<http://www.initos.com>).
# Copyright 2016 Tecnativa - Vicent Cubells
# Copyright 2016 Camptocamp - Akim Juillerat (<http://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, exceptions, _


class ResPartner(models.Model):
    """Assigns 'ref' from a sequence on creation and copying"""

    _inherit = 'res.partner'

    @api.multi
    def _get_next_ref(self, vals=None):
        return self.env['ir.sequence'].next_by_code('res.partner')

    @api.multi
    def _generate_ref(self, vals=None):
        if not vals and not self:  # pragma: no cover
            raise exceptions.UserError(_(
                'Either field values or an id must be provided.'))
        res_partner_obj = self.env['res.partner']
        res_partner_type_obj = self.env['res.partner.company.type']
        if self or vals.get('company_group_id') or vals.get('partner_company_type_id'):
            company_group_id = vals.get('company_group_id', self.company_group_id.id)
            company_type_id = vals.get('partner_company_type_id', self.partner_company_type_id.id)
            group_code = ''
            type_code = ''
            sequence = self._get_next_ref(vals=vals)
            if company_group_id:
                group_code = res_partner_obj.browse(company_group_id).group_code
            if company_type_id:
                type_code = res_partner_type_obj.browse(company_type_id).shortcut
            return group_code + type_code + sequence

    @api.model
    def create(self, vals):
        if not vals.get('ref') and self._needsRef(vals=vals):
            vals['ref'] = self._generate_ref(vals=vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def copy(self, default=None):
        default = default or {}
        if self._needsRef():
            default['ref'] = self._generate_ref(vals={})
        return super(ResPartner, self).copy(default)

    @api.multi
    def write(self, vals):
        for partner in self:
            partner_vals = vals.copy()
            if (partner._needsRef(partner_vals)
            ):
                partner_vals['ref'] = partner._generate_ref(vals=partner_vals)
            super(ResPartner, partner).write(partner_vals)
        return True

    @api.multi
    def _needsRef(self, vals=None):
        """
        Checks whether a sequence value should be assigned to a partner's 'ref'

        :param vals: known field values of the partner object
        :return: true iff a sequence value should be assigned to the\
                      partner's 'ref'
        """
        if not vals and not self:  # pragma: no cover
            raise exceptions.UserError(_(
                'Either field values or an id must be provided.'))
        # only assign a 'ref' to commercial partners
        if self:
            vals = {}
            vals['is_company'] = self.is_company
            vals['parent_id'] = self.parent_id
            vals['ref'] = self.ref
        return not vals.get('parent_id')

    @api.model
    def _commercial_fields(self):
        """
        Make the partner reference a field that is propagated
        to the partner's contacts
        """
        return super(ResPartner, self)._commercial_fields() + ['ref']
