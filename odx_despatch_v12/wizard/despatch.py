# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools
from datetime import datetime,timedelta

class od_despatch_wizard(models.TransientModel):
	_name = "od.despatch.wizard"
	_description = "despatch"

	date_from = fields.Date('Date From',required=True)
	date_to = fields.Date('Date To',required=True,default=fields.Date.context_today)
	
	@api.multi
	def od_gen(self):
		existing_ids = self.env['od.despatch.datewise'].search([])
		existing_ids.unlink()
		invoice = self.env['account.invoice']
		invoice_ids = invoice.search([('od_despatch_date','>=',self.date_from),('od_despatch_date','<=',self.date_to)])	

		for lines in invoice_ids:
			des_rf = lines.despath_move_id.name
			if lines.despath_move_id.ref:
				des_rf = des_rf + "(" + lines.despath_move_id.ref + ")"
			vals = {'od_despatch_date':lines.od_despatch_date or False,
					'partner_id':lines.partner_id.id or False,
					'od_despatch_ref_id':des_rf or False,
					'number':lines.number or False,
					'date_invoice':lines.date_invoice or False,
					'amount_total':lines.amount_total or False,
					'od_transport_type':lines.od_transport_type or False,
					'od_transporter_id':lines.od_transporter_id.id or False,
					'od_trans_ref':lines.od_trans_ref or False,
					'od_amount':lines.od_amount or False
					}
			vals['no_ofcarton'] = 0
			for dispatch in lines.od_dispatch_line:
				vals['no_ofcarton'] = vals['no_ofcarton'] + (dispatch.no_ofcarton or False)
			self.env['od.despatch.datewise'].create(vals)
					   

		return {
			'name':'Despatch',
			'view_type': 'form',
			'view_mode': 'tree,pivot',
			'res_model': 'od.despatch.datewise',
			'type': 'ir.actions.act_window',
		}
