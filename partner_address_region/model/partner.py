# © 2014-2016 Camptocamp SA
# @author: Nicolas Bessi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    """Add third field in address"""
    _inherit = "res.partner"

    region_id = fields.Many2one(comodel_name='res.country.region', string='Region')

    @api.model
    def _address_fields(self):
        fields = super(ResPartner, self)._address_fields()
        fields.append('region_id')
        return fields

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(region_name)s\n%(country_name)s"

    @api.multi
    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'region_name': self.region_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {'domain': {'state_id': [('country_id', '=', self.country_id.id)],
                               'region_id': [('country_id', '=', self.country_id.id)]}}
        else:
            return {'domain': {'state_id': [], 'region_id': []}}

    @api.onchange('region_id')
    def _onchange_region_id(self):
        if self.region_id:
            return {'domain': {'state_id': [('country_id', '=', self.country_id.id)]}}
        else:
            return {'domain': {'state_id': []}}


class CountryRegion(models.Model):
    _description = "Country region"
    _name = 'res.country.region'
    _order = 'code'

    country_id = fields.Many2one('res.country', string='Country', required=True)
    name = fields.Char(string='Region Name', required=True)
    code = fields.Char(string='Region Code', help='The region code.', required=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(country_id, code)', 'The code of the region must be unique by country !')
    ]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        if self.env.context.get('country_id'):
            args = args + [('country_id', '=', self.env.context.get('country_id'))]
        first_region_ids = self._search([('code', '=ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        search_domain = [('name', operator, name), ('id', 'not in', first_region_ids)]
        region_ids = first_region_ids + self._search(search_domain + args, limit=limit, access_rights_uid=name_get_uid)
        return [(region.id, region.display_name) for region in self.browse(region_ids)]


class CountryState(models.Model):
    _inherit = 'res.country.state'

    region_id = fields.Many2one(comodel_name='res.country.region', string='Region')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        if self.env.context.get('region_id'):
            args = args + [('region_id', '=', self.env.context.get('region_id'))]
        return super(CountryState, self)._name_search(name, args, operator=operator, limit=limit,
                                                      name_get_uid=name_get_uid)
