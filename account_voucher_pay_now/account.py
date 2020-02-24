#-*- coding:utf-8 -*-

from odoo import models, fields, api

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'
    
    pay_now = fields.Selection(default='pay_now')