# -*- coding: utf-8 -*-
from odoo import models,api,fields


class od_cartonsize(models.Model):
    _name = "od.cartonsize"
    name = fields.Char(string='Name')
    
class State(models.Model):
    _inherit = "res.country.state"
    od_transit_days = fields.Integer(string='Transit Days')



class od_transporter_pricelist(models.Model):
    _name = "od.transporter.pricelist"
    name = fields.Char(string='Name')
    transporter_id = fields.Many2one('res.partner',string='Transporter')
    state_id = fields.Many2one('res.country.state',string='State')
    unit_price = fields.Float(string='Unit Price')
    od_cartonsize_id = fields.Many2one('od.cartonsize',string='Carton Size')
    
    

        
      

    _sql_constraints = [
        ('name_uniq', 'unique(transporter_id, state_id, od_cartonsize_id)', 'pricelist already exisisting'),
    ]
