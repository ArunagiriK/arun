from odoo import models,fields,api

class ResCompany(models.Model):
    _inherit = 'res.company'


    @api.model
    def update_periodic_lock_date(self):
        today = fields.Date.from_string(fields.Date.today())
        for company in self.search([]):
            company.period_lock_date = today
