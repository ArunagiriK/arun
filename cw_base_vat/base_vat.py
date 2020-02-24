# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    country_code = fields.Char(related='country_id.code', readonly=True)
    

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id and self.state_id.country_id.id or False
            self.country_code = self.state_id.country_id and self.state_id.country_id.code or False            
          
    

    @api.onchange('country_id')
    def _onchange_country_id(self):
        res = super(ResPartner, self)._onchange_country_id()
        if self.country_id:
            self.country_code = self.country_id.code            
            if self.state_id and self.state_id.country_id != self.country_id:
                self.state_id = False            
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: