# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class HrGrade(models.Model):
    _name = "hr.grade"
    _order = "id desc"
    
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
    
    _sql_constraints = [
        ('code_company_uniq', 'unique (code, company_id)', 'The code of the grade must be unique per company!'),
    ]