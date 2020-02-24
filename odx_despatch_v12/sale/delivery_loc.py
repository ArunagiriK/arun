# -*- coding: utf-8 -*-
from odoo import models,api,fields

class od_delivery_loc(models.Model):
    _name = "od.delivery.loc"
    name = fields.Char(string='Name')


