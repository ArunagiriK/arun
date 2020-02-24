# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from itertools import groupby
import operator
import pandas as pd
from datetime import datetime,timedelta


class DespatchNewWizard(models.TransientModel):
	_name = "od.despatch.new.wizard"
	_description = 'DespatchNewWizard' 
	
	@api.multi
	@api.onchange('od_transporter_id','transport_charge','od_state_id','wizard_line.no_of_carton')
	def onchange_od_packaging_type_id(self):
		wizard_line = self.wizard_line
		transport_charge = self.transport_charge
		for wiz in wizard_line:
			wiz.transportation_charge = transport_charge
			wiz.amount = transport_charge * wiz.no_of_carton

		

	@api.onchange('od_state_id')
	def onchange_od_state(self):
		pricelist_obj = self.env['od.transporter.pricelist'].search([])
		state_id = [] 
		for res in pricelist_obj:
			for states in res.state_id:
				state_id.append(states.id)
		return {
			'domain': {'od_state_id': [('id', 'in', state_id)]}
		}

	def distribute(self):
		if not self.transporter_ref:
			raise UserError(_('Please add transporter ref!!')) 
		total_carton = self.total_carton
		transport_charge = self.transport_charge
		tot_inv = 0
		wizard_line = self.wizard_line
		for wiz in wizard_line:
			tot_inv = tot_inv + wiz.invoice_id.amount_total
		for line in wizard_line:
			no_of_carton = float(line.invoice_id.amount_total / tot_inv) * total_carton
			line.no_of_carton = no_of_carton
			line.amount = no_of_carton * transport_charge
			line.tranfer_ref = self.transporter_ref
			
		
		



		return {
			'name':'Despatch',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'od.despatch.new.wizard',
			'res_id': self.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		} 
		
		
	def process(self):
		if not self.notify:
			raise UserError(_('Please Verify!!')) 
		od_transporter_id = self.od_transporter_id and self.od_transporter_id.id or False
		od_despatch_date = self.od_despatch_date
		
		od_delivery_assis_ids = self.od_delivery_assis_ids
		users = []
		for addrs in od_delivery_assis_ids:
			users.append(addrs and addrs.id)
		od_driver_id = self.od_driver_id and self.od_driver_id.id
		od_despatch_desc = self.od_despatch_desc
		od_transport_type = self.od_transport_type
		od_state_id = self.od_state_id and self.od_state_id.id
		od_fleet_id = self.od_fleet_id and self.od_fleet_id.id
		transport_charge = self.transport_charge
		
		if od_transport_type == 'own':
			if not od_state_id or not od_driver_id or not od_fleet_id or not od_despatch_date:
				raise UserError(_('Please fill all the details'))  
				
		if od_transport_type == 'third':
			if not od_state_id or not od_driver_id or not od_fleet_id or not od_despatch_date or not transport_charge:
				raise UserError(_('Please fill all the details'))         
		




		transport_charge = self.transport_charge
		wizard_line = self.wizard_line
		so_wizard_line = self.so_wizard_line
		name = self.name
		document_date = self.document_date
		combine = self.combine
		notify = self.notify
		transporter_ref = self.transporter_ref
		total_carton = self.total_carton
		total_amount = self.total_amount
		
		wiz_line_values = []
		for line in wizard_line:
			line.invoice_id.od_despatch_state = 'despatched'
			line.invoice_id.od_transporter_id = od_transporter_id
			line.invoice_id.od_state_id = od_state_id
			line.invoice_id.od_despatch_date = od_despatch_date
			line.invoice_id.od_fleet_id = od_fleet_id
			
			vals = (0,0,{'invoice_id':line.invoice_id and line.invoice_id.id or False,
			'partner_id':line.partner_id and line.partner_id.id or False,
			'tranfer_ref':line.tranfer_ref,
			'no_of_carton':line.no_of_carton,
			'transportation_charge':line.transportation_charge,
			'amount':line.amount})
			wiz_line_values.append(vals)
			

			
		so_wizard_line_values = []
		for line in so_wizard_line:
			vals = (0,0,{'so_id':line.so_id and line.so_id.id or False,
			'partner_id':line.partner_id and line.partner_id.id or False,
			'date':line.date,
			'requested_date':line.requested_date,
			'amount':line.amount,
			'state_id':line.state_id and line.state_id.id})
			so_wizard_line_values.append(vals)
#        for add in od_delivery_assis_ids:


		
		vals = {'name':name,
				'od_transporter_id':od_transporter_id,
				'od_despatch_date':od_despatch_date,
				'document_date':document_date,
				'od_transport_type':od_transport_type,
				'od_state_id':od_state_id,
				'od_driver_id':od_driver_id,
				'od_despatch_desc':od_despatch_desc,
				'od_fleet_id':od_fleet_id,
				'transport_charge':transport_charge,
				'combine':combine,
				'notify':notify,
				'transporter_ref':transporter_ref,
				'total_carton':total_carton,
				'total_amount':total_amount,
				'checklist_line':wiz_line_values,
				'checklist_so_line':so_wizard_line_values,
				'od_delivery_assis_ids':[(6, 0, users)]}
			
			
		checklist_id = self.env['od.despatch.checklist'].create(vals)
#        for add in od_delivery_assis_ids:
#            vals = {'line_id':checklist_id.id,
#            'user_id':add.user_id and add.user_id.id}
#            self.env['rel.invoice.despath.user.checklist'].create(vals)
			
		
		
		
		if so_wizard_line_values:
			if not notify:
				raise UserError(_('Please tick the notify check box'))  
		
		action = self.env.ref('odx_despatch_v12.od_despatch_checklist_action').read()[0]
		return action
		
	
	
	   
	
	
#    @api.model
#    def default_get(self, fields_list):
#        print "11111111111111111111111111111",self._context.get('active_id')
#        res = super(DespatchNewWizard, self).default_get(fields_list)
#        print "11111111111111111111111111111",self._context.get('active_id')
##        move_obj = self.env['stock.move'].browse(self._context.get('active_id'))
##        product_id = move_obj.product_id and move_obj.product_id.id
##        od_packaging_type_id = move_obj.od_packaging_type_id and move_obj.od_packaging_type_id.id or False
##        picking_obj = move_obj.picking_id
##        # if move_obj.od_package_id:
##        #     raise Warning("already scanned it")
##            
##        picking_type_obj = picking_obj.picking_type_id
##        default_location_src_id = picking_type_obj.default_location_src_id and picking_type_obj.default_location_src_id.id
##        product_ids = [move_obj.product_id and move_obj.product_id.id]
###        move_lines = picking_obj.move_lines
###        for pack in move_lines:
###            product_ids.append(pack.product_id.id)
##        active_model = self._context.get('active_model')
##        res.update({'product_ids': [(6,0,product_ids)],'location_id':default_location_src_id,'move_id':move_obj.id,'product_id':product_id,'packaging_type_id':od_packaging_type_id})
#        return res
	
	

	@api.depends('od_transporter_id', 'od_state_id')
	def _compute_transport_charge(self):
	
		od_transporter_id = self.od_transporter_id and self.od_transporter_id.id
		od_state_id = self.od_state_id and self.od_state_id.id
		if od_transporter_id and od_state_id:
			pricelist = self.env['od.transporter.pricelist'].search([('transporter_id','=',od_transporter_id),('state_id','=',od_state_id)])
			if len(pricelist):
				pricelist = pricelist[0]
				self.transport_charge = pricelist.unit_price or 0
	
			  




	
	def default_od_journal_id(self):
		journal_id = False
		journal = self.env['account.journal']
		journal_ob = journal.search([('name','=','JOURNAL VOUCHER')])
		if journal_ob:
			journal_id = journal_ob.id
		return journal_id
	od_transporter_id = fields.Many2one('res.partner', string='Transporter',domain=[('supplier','=',True)])       
	od_despatch_date = fields.Datetime(string="Despatch Date")        
#    od_journal_id = fields.Many2one('account.journal',string="Journal",default=default_od_journal_id)       
	od_transport_type = fields.Selection([('own','Own Transportation'),('third','Third Party')],string="Transportation Type",default='own')
	od_state_id = fields.Many2one('res.country.state', string='Destination')
	
	od_driver_id = fields.Many2one('res.users', string='Driver')
	od_delivery_assis_ids = fields.Many2many('res.users','rel_invoice_despath_user_wizard','wizard_id','user_id',string="Delivery Assistant")
	od_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle Reg No")
	
	transport_charge = fields.Float(compute='_compute_transport_charge', string='Transportaion Charge', readonly=True, store=True)
	wizard_line = fields.One2many('od.despatch.new.wizard.line','wizard_id',string="Wizard Line")
	so_wizard_line = fields.One2many('od.despatch.new.wizard.so.line','wizard_id',string="So Wizard Line")
	name = fields.Char(string='Name')
	combine = fields.Boolean(string='Combine')
	notify = fields.Boolean(string='Verified')
	transporter_ref = fields.Char(string='Transporter Ref')
	total_carton = fields.Float(string='Total Carton')
	total_amount = fields.Float(string='Total Amount')
	name = fields.Char(string="Sequence")
	document_date = fields.Date(string="Document Date")
	
	od_despatch_desc =fields.Char(string="Despatch Description")
	

	
	
	
	
	
class DespatchNewWizardLine(models.TransientModel):
	_name = "od.despatch.new.wizard.line"
	_description = 'DespatchNewWizardLine' 
	
	@api.depends('transportation_charge', 'wizard_id','no_of_carton')
	def _compute_amount(self):
	
		for line in self:

			line.amount = line.transportation_charge * line.no_of_carton
				
			
	
	wizard_id = fields.Many2one('od.despatch.new.wizard',string="Wizard") 
	invoice_id = fields.Many2one('account.invoice',string="Invoice") 
	partner_id = fields.Many2one('res.partner',string="Partner")  
	tranfer_ref = fields.Char(string='Transporter Ref') 
	no_of_carton = fields.Float(string="No.Of.Carton") 
	transportation_charge = fields.Float(string='Tran.Charge')
	
	

	amount = fields.Float(compute='_compute_amount',string="Amount")
	
	
class DespatchNewWizardSoLine(models.TransientModel):
	_name = "od.despatch.new.wizard.so.line"
	_description = 'DespatchNewWizardSoLine' 
	wizard_id = fields.Many2one('od.despatch.new.wizard',string="Wizard") 
	partner_id = fields.Many2one('res.partner',string="Customer") 
	so_id = fields.Many2one('sale.order',string="Quotation/So") 
	client_order_ref = fields.Char(string='Customer Reference')
	date = fields.Date(string="Date")
	requested_date = fields.Date(string="Requested Date")
	amount = fields.Float(string="Amount")
	state_id = fields.Many2one('res.country.state',string="State")    
	
	
	
	
	
	
	
	
	


	
	
