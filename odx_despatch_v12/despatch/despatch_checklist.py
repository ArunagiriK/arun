# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, tools
from odoo import models,api,fields
from odoo.exceptions import Warning,RedirectWarning
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DespatchCheckList(models.Model):
	_name ='od.despatch.checklist'
	
	

	
	state = fields.Selection([
		('despatch', 'Despatch'),
		('posted', 'Posted'),
		], string='Status',default='despatch')
	
	name = fields.Char(string='Name') 
	document_date = fields.Date(string="Document Date")
	od_transporter_id = fields.Many2one('res.partner', string='Transporter')       
	od_despatch_date = fields.Datetime(string="Despatch Date")        
	od_journal_id = fields.Many2one('account.journal',string="Journal")       
	od_transport_type = fields.Selection([('own','Own Transportation'),('third','Third Party')],string="Transportation Type",default='own')
	od_state_id = fields.Many2one('res.country.state', string='Destination')
	
	od_driver_id = fields.Many2one('res.users', string='Driver')
	od_delivery_assis_ids = fields.Many2many('res.users','rel_invoice_despath_user_checklist','line_id','user_id',string="Delivery Assistant")
	od_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle Reg No")
	
	transport_charge = fields.Float(string='Transportaion Charge')
	checklist_line = fields.One2many('od.despatch.checklist.line','line_id',string="Checklist Line")
	checklist_so_line = fields.One2many('od.despatch.checklist.so.line','line_id',string="Checklist So Line")
	combine = fields.Boolean(string='Combine')
	notify = fields.Boolean(string='Notify')
	transporter_ref = fields.Char(string='Transporter Ref')
	total_carton = fields.Float(string='Total Carton')
	total_amount = fields.Float(string='Total Amount')
	expense_account_id = fields.Many2one('account.account',string="Expense Account")

	od_despatch_desc = fields.Char(string='Despatch Description')
	od_mail_sent = fields.Boolean(string='Mail Sent')
	
	
	def od_send_mail(self,template,data,ctx_mail):
		ir_model_data = self.env['ir.model.data']
		mail_obj = self.env['mail.template']
		template_id = ir_model_data.get_object_reference('odx_despatch_v12', template)[1]
		template = mail_obj.browse(template_id)
		user = self.env.user
		context = self.env.context
		ctx  = context.copy()
		ctx['data'] = data
		ctx.update(ctx_mail)
		template.with_context(ctx).send_mail(user.id,force_send=True)
		return True

	@api.multi
	def send_report(self):
		self.od_mail_sent = True
		today = datetime.today().strftime('%Y-%m-%d')
		despatch_line = self.checklist_line
		date = datetime.strptime(self.od_despatch_date,'%Y-%m-%d %H:%M:%S')
		Date = date.strftime('%d-%m-%Y')
		despatch_desc = self.od_despatch_desc
		partner = despatch_line[0].partner_id and despatch_line[0].partner_id.name
		sales_person = despatch_line[0].partner_id and despatch_line[0].partner_id.user_id and despatch_line[0].partner_id.user_id.name
		driver = self.od_driver_id and self.od_driver_id.name
		transporter = self.od_transporter_id and self.od_transporter_id.name
		div_mgr_mail = despatch_line[0].partner_id and despatch_line[0].partner_id.od_division_id and despatch_line[0].partner_id.od_division_id.div_mgr_id.login or ''
		salesman_mail = despatch_line[0].partner_id and despatch_line[0].partner_id.user_id.login or ''
		data = {'despatch_date':Date,
			'partner_id':partner,
			'salesman':sales_person,
			'despatch_desc':despatch_desc}
		filter_trans = {}
		if self.od_transport_type == 'third':
			filter_trans['filter'] = transporter
			data.update(filter_trans)
		else:
			filter_trans['filter'] = driver
			data.update(filter_trans)
		data['invoice_list'] = []
		data['reference_list'] = []
		tot_carton = 0
		for line in despatch_line:
			tot_carton+=line.no_of_carton
			data['total_carton']= tot_carton
			data['invoice_list'].append(str(line.invoice_id.number ))
			data['reference_list'].append(str(line.invoice_id.name))
		data['invoice'] = ','.join(data['invoice_list'])
		data['reference'] = ','.join(data['reference_list'])
		ctx_mail = {}
		ctx_mail['cur_date'] = today
		ctx_mail['email_to'] = div_mgr_mail
		ctx_mail['email_cc'] = salesman_mail
		self.od_send_mail('email_bfly_despatch_checklist_report',data,ctx_mail) 

	def posted(self):
		despatch_line = self.checklist_line
		journal_id = self.od_journal_id and self.od_journal_id.id
		date = self.od_despatch_date or self.document_date 
		name = self.name
		move_vals = {'journal_id':journal_id,'date':date,'ref': 'Despatch' + _(' :: ') + str(name)}
		trans_id = self.od_transporter_id and self.od_transporter_id.id
		partner_id = despatch_line[0].partner_id and despatch_line[0].partner_id.id
		od_division_id = despatch_line[0].partner_id and despatch_line[0].partner_id.od_division_id.id or False
		payable_acc_id = self.od_transporter_id and self.od_transporter_id.property_account_payable_id and self.od_transporter_id.property_account_payable_id.id or False
		expense_account_id = self.expense_account_id and self.expense_account_id.id
		if not expense_account_id or not payable_acc_id or not journal_id:
			raise UserError(_('check accounts and journal configured correctly')) 
			



		for line in despatch_line:
			move_line = []
			move_line_paid = []
			move_pool = self.env['account.move']
			if not line.tranfer_ref:
				raise UserError(_('no transfer ref found'))
			line1 = (0,0,{'account_id':expense_account_id, 'orchid_cc_id':od_division_id, 'partner_id':partner_id,'name':line.tranfer_ref + " " + str(line.invoice_id.number + line.invoice_id.name ),'credit':0.0,'debit':line.amount})
			line2 = (0,0,{'account_id':payable_acc_id,'partner_id':trans_id,'name':line.tranfer_ref + " " + str(line.invoice_id.number + line.invoice_id.name),'credit':line.amount,
				'debit':0})
			move_line.append(line1)
			move_line.append(line2)
			move_vals['line_ids'] = move_line
			move = move_pool.create(move_vals)
			move.post()  
			line.invoice_id.despath_move_id = move.id   
			self.env['od.dispatch.info.line'].create({'inv_id':line.invoice_id and line.invoice_id.id,'unit_price':line.transportation_charge,'no_ofcarton':line.no_of_carton,'amount':line.amount}) 
			line.invoice_id.od_transport_type = self.od_transport_type 	
			line.invoice_id.od_transporter_id = trans_id
			line.invoice_id.od_journal_id = self.od_journal_id and self.od_journal_id.id			
			line.invoice_id.od_despatch_date = self.od_despatch_date
			line.invoice_id.od_driver_id = self.od_driver_id and self.od_driver_id.id	
			line.invoice_id.od_fleet_id = self.od_fleet_id and self.od_fleet_id.id
			line.invoice_id.od_trans_ref = line.tranfer_ref
			users = []
			for addrs in self.od_delivery_assis_ids:
				
				users.append(addrs and addrs.id)
			line.invoice_id.od_delivery_assis_ids = [(6, 0, users)]
			
		 
		self.state = 'posted'
	
class DespatchCheckListLine(models.Model):
	_name ='od.despatch.checklist.line'

				
			
	
	line_id = fields.Many2one('od.despatch.checklist',string="Checklist") 
	invoice_id = fields.Many2one('account.invoice',string="Invoice") 
	partner_id = fields.Many2one('res.partner',string="Partner")  
	tranfer_ref = fields.Char(string='Transporter Ref') 
	no_of_carton = fields.Float(string="No.Of.Carton") 
	transportation_charge = fields.Float(string='Tran.Charge')
	
	

	amount = fields.Float(string="Amount")
	
class DespatchCheckListSoLine(models.Model):
	_name ='od.despatch.checklist.so.line' 
	line_id = fields.Many2one('od.despatch.checklist',string="Checklist") 
	partner_id = fields.Many2one('res.partner',string="Customer") 
	so_id = fields.Many2one('sale.order',string="Quotation/So") 
	client_order_ref = fields.Char(string='Customer Reference')
	date = fields.Date(string="Date")
	requested_date = fields.Date(string="Requested Date")
	amount = fields.Float(string="Amount")
	state_id = fields.Many2one('res.country.state',string="State")  
