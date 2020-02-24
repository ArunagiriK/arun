# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools


class Partner(models.Model):
    _inherit = 'res.partner' 
    
    #od_analytic_account_id = fields.Many2one('account.analytic.account',string="Analytic Account")


class PartnerArea(models.Model):
    _name = "orchid.partner.area"

    name = fields.Char(string='Name')
    description = fields.Text(string='Desc')
    seq = fields.Integer(string="Sequence")


class PartnerGroup(models.Model):
    _name = "orchid.partner.group"
    name = fields.Char(string='Name')
    description = fields.Text(string='Desc')



class CustomerCategory(models.Model):
    _name = 'orchid.category'
    name = fields.Char(string="Category")
    code = fields.Char(string="code",size=2,readonly=False,required=True,default='/')

