# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class HrJob(models.Model):
    _inherit = "hr.job"
    
    code = fields.Char('Code', required=True)    
    #exclude_annual_leave = fields.Boolean(string='Exclude Annual Leave')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
    
    _sql_constraints = [
        ('code_company_uniq', 'unique (code, company_id)', 'The code of the job must be unique per company!'),
    ]