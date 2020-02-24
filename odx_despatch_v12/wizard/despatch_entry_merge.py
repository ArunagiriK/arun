# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools
from datetime import datetime,timedelta

from odoo.exceptions import UserError
from datetime import date

class depatch_entry_merge(models.TransientModel):
	_name = "despatch.entry.merge"
	_description = "Despatch Entry Merge"

	@api.model
	def default_get(self, default_fields):
		res = super(depatch_entry_merge, self).default_get(default_fields)
		invoices = self.env['account.invoice'].search([('id', 'in',self.env.context.get('active_ids'))])
		if invoices:
			transporter = invoices[0].od_transporter_id
			despatch_journal = invoices[0].od_journal_id
			despatch_debit_account = invoices[0].od_trans_acc_id
			despatch_credit_account = invoices[0].od_transporter_id.property_account_payable_id
			amount = 0
			for record in invoices:
				if record.od_transporter_id.id != transporter.id:
					raise UserError('Only similar Transportes can be merged to one despatch entry')
				if record.od_despatch_state == 'despatched':
					raise UserError('Despatched invoices cannot be depatched again')
				# if not self.depatch_journal_id and record.od_journal_id.id != despatch_journal.id:
				# 	raise UserError('Only similar Journal can be used to one despatch entry')
				# if not self.debit_account_id and record.od_trans_acc_id.id != despatch_debit_account.id:
				# 	raise UserError('Only similar Debit Account can be used to one despatch entry')
				# if not self.credit_account_id and record.od_transporter_id.property_account_payable_id.id != despatch_credit_account.id:
				# 	raise UserError('Only similar Credit Account can be used to one despatch entry')
				amount += record.od_amount
			res['amount'] = amount
			res['transporter_id'] = transporter.id
			res['debit_account_id'] = despatch_debit_account.id
			res['credit_account_id'] = despatch_debit_account.id
			res['debit_account_id'] = despatch_credit_account.id
			res['despatch_journal_id'] = despatch_journal.id
		return res



	transporter_id = fields.Many2one('res.partner',string='Transporter',readonly=True,required=False)
	amount = fields.Float('Amount',readonly=True,required=True)
	despatch_journal_id = fields.Many2one('account.journal',string='Journal',required=True)
	debit_account_id = fields.Many2one('account.account',string='Debit Account',required=True)
	credit_account_id = fields.Many2one('account.account',string='Credit Account',required=True)

	@api.multi
	def generate_despatch_entry(self):
		invoices = self.env['account.invoice'].search([('id', 'in',self.env.context.get('active_ids'))])
		move_obj = self.env['account.move']
		if invoices:
			print(invoices)
			transporter=invoices[0].od_transporter_id
			despatch_journal = invoices[0].od_journal_id
			despatch_debit_account = invoices[0].od_trans_acc_id
			despatch_credit_account = invoices[0].od_transporter_id.property_account_payable_id
			amount=0
			for record in invoices:
				if record.od_transporter_id.id != transporter.id:
					raise UserError('Only similar Transportes can be merged to one despatch entry')
				if record.od_despatch_state =='despatched':
					raise UserError('Despatched invoices cannot be depatched again')
				if not self.despatch_journal_id and record.od_journal_id_id.id != despatch_journal.id:
					raise UserError('Only similar Journal can be used to one despatch entry')
				if not self.debit_account_id and record.od_trans_acc_id.id != despatch_debit_account.id:
					raise UserError('Only similar Debit Account can be used to one despatch entry')
				if not self.credit_account_id and record.od_transporter_id.property_account_payable_id.id != despatch_credit_account.id:
					raise UserError('Only similar Credit Account can be used to one despatch entry')
				amount +=record.od_amount
				record.update({'od_despatch_state':'despatched',
							   'od_desp_confirm':True})
			self.debit_account_id = despatch_debit_account.id
			self.credit_account_id = despatch_debit_account.id
			self.debit_account_id = despatch_credit_account.id
			self.despatch_journal_id = invoices[0].od_journal_id.id

			move_lines = []

			vals1 = {
				'name': 'Merged Despatch Entry',
				'ref': 'Merged Despatch Entry',
				'journal_id': self.despatch_journal_id.id,
				'date': date.today(),
				'account_id': self.credit_account_id.id,
				'debit': 0.0,
				'credit': abs(amount),
				'partner_id': self.transporter_id and self.transporter_id.id or False,

			}
			vals2 = {
				'name': 'Merged Despatch Entry',
				'ref': 'Merged Despatch Entry',
				'journal_id': self.despatch_journal_id.id,
				'date': date.today(),
				'account_id': self.debit_account_id.id,
				'credit': 0.0,
				'debit': abs(amount),
				'partner_id': self.transporter_id and self.transporter_id.id or False,

			}
			move_lines.append([0, 0, vals1])
			move_lines.append([0, 0, vals2])

			move_vals = {

				'date': date.today(),
				'ref': 'Merged Despatch Entry',
				'journal_id': self.despatch_journal_id.id,
				'line_ids': move_lines

			}
			move = move_obj.create(move_vals)
			move.post()
			move_id = move.id

			return {
				'name':'Despatch',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'account.move',
				'res_id':move_id,
				'type': 'ir.actions.act_window',
			}
		else:
			raise UserError('Select invoices with Despatch values')
