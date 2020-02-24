# -*- coding: utf-8 -*-
from odoo import models,api,fields

class orchid_division_target(models.Model):
    _name = "orchid.division.target"
    _rec_name ='division_id'

    division_id = fields.Many2one('orchid.account.cost.center',string='Division')
    category_id = fields.Many2one('orchid.category',string='Category')
    sale_target = fields.Float(string="Sales Target")
    
    _sql_constraints = [
        ('div_categ_id_uniq', 'unique(division_id,category_id)',
            'Divsion Category Target is Unique'),
    ]
