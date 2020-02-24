# -*- coding: utf-8 -*-
from odoo import models,api,fields
import itertools


class Partner(models.Model):
	_inherit = 'res.partner'

	od_sale_target = fields.Float(string="Sales Target")
	od_invoice_print = fields.Char("Invoice Print Name")
	od_journal_id = fields.Many2one('account.journal',string="Journal")


class PartnerArea(models.Model):
	_inherit = "orchid.partner.area"
	
	salesman_line = fields.One2many('orchid.partner.area.salesman.line', 'area_line_id', string='Salesman Lines')


class PartnerAreaSalesmanLine(models.Model):
	_name = "orchid.partner.area.salesman.line"

	area_line_id = fields.Many2one('orchid.partner.area', string='Area')
	od_salesman_id = fields.Many2one('res.users',string='Sales Man',required= True)
	od_target = fields.Float(string='Target Value',required= True)


class PartnerGroup(models.Model):
	_inherit = "orchid.partner.group"

	od_target = fields.Float(string="Target Value",required= True)	
	od_code = fields.Char(string="code",size=2,readonly=False,required=True,default='/')


class State(models.Model):
	_inherit = "res.country.state"

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		context = self._context or {}

		if context.get('od_despatch'):
			trans_pricelist = self.env['od.transporter.pricelist']
			states = [tr.state_id.id for tr in trans_pricelist.search([])]
			state_ids = list(set(states))
			args += [('id', 'in', state_ids)]
		return super(State, self).search(args, offset, limit, order, count=count)
	