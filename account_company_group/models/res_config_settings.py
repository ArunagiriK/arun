# -*- coding: utf-8 -*-

from odoo import fields, models,api,_
import ast



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_ids = fields.Many2many('res.company', string='Child Companies')
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        companies = str(self.env['ir.config_parameter'].sudo().get_param('account_company_group.company_ids'))
        res.update(
            company_ids=[(6, 0, eval(companies))],
        )
        return res
    
    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('account_company_group.company_ids', self.company_ids.ids)
    

    #~ def set_values(self):
        #~ super(ResConfigSettings, self).set_values()
        #~ res = self.env['ir.config_parameter'].set_param('account_company_group.company_ids', self.company_ids)

    #~ @api.model
    #~ def get_values(self):
        #~ res = super(ResConfigSettings, self).get_values()
        #~ ICPSudo = self.env['ir.config_parameter'].sudo()
        #~ companies = ICPSudo.get_param('account_company_group.company_ids')
        #~ res.update(
            #~ company_ids= companies,
        #~ )
        #~ return res

    
