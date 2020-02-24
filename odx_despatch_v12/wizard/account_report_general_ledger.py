# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlwt
from io import StringIO
import base64

class AccountReportGeneralLedger(models.TransientModel):
	_inherit = "account.report.general.ledger"

	od_currency_id = fields.Many2one('res.currency',string ="Currency")

	@api.multi
	def check_report(self):
		result = super(AccountReportGeneralLedger,self).check_report()
		result['od_currency_id'] = self.od_currency_id.id or False
		return result
	def _print_report(self, data):
		result = super(AccountReportGeneralLedger,self)._print_report(data)
		result['data']['od_currency_id'] =self.od_currency_id.id or False
		return result 



	def print_excel(self):
		filename= 'GeneralLedger.xls'
		ctx = self.env.context
		data = self.get_data_for_xls()
		sortby = data['form']['sortby']
		init_balance = data['form']['initial_balance']
		date_from =  data['form']['date_from']
		date_to =  data['form']['date_to']
		od_move_lines = self.get_move_line_ids()
		od_move_lines = self.env['account.move.line'].browse(od_move_lines)
		search_cond = '''  '''
		od_currency_id = self.od_currency_id.id or False
		
		if od_move_lines:
			search_cond = search_cond + ''' and l.id in %s '''
					
		if data['form'].get('journal_ids', False):
			codes = [journal.code for journal in self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
		self.model = self.env.context.get('active_model')
		accounts = self.env['account.account'].browse(ctx.get('active_id')) if self.model == 'account.account' else self.env['account.account'].search([])
		display_account = data['form']['display_account']
		used_context = self._build_contexts(data)
		data['form']['used_context'] = dict(used_context, lang=ctx.get('lang', 'en_US'))
		movelines = self.env['report.account.report_generalledger'].with_context(data['form'].get('used_context',{}))._get_account_move_entry( accounts, init_balance, sortby, display_account,od_move_lines,search_cond,od_currency_id)
		workbook= xlwt.Workbook(encoding="UTF-8")
		sheet= workbook.add_sheet('General Ledger Report',cell_overwrite_ok=True)
		style = xlwt.easyxf('font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')
		style_filter = xlwt.easyxf('font:name Arial; align: horiz center, vert center;')
		a = range(1,10)
		row = 0
		col = 0
		style2 = xlwt.easyxf('font: bold 1')
		sheet.write(row,0,"Date",style2)
		sheet.write(row,1,"JRNL",style2)
		sheet.write(row,2,"Partner",style2)
		sheet.write(row,3,"Ref",style2)
		sheet.write(row,4,"Move",style2)
		sheet.write(row,5,"Entry Label",style2)
		sheet.write(row,6,"Debit",style2)
		sheet.write(row,7,"Credit",style2)
		sheet.write(row,8,"Balance",style2)
		
		row = 1
		for index,data in enumerate(movelines):
			name = data.get('name')
			total_credit = data.get('credit')
			total_debit = data.get('debit')
			total_balance = data.get('balance')
			sheet.write(row,0,name,style2)
			sheet.write(row,6,total_debit,style2)
			sheet.write(row,7,total_credit,style2)
			sheet.write(row,8,total_balance,style2)
			row = row +  1
			for inner_index,data1 in enumerate(data.get('move_lines')):
				date = data1.get('ldate')
				lcode = data1.get('lcode')
				partner_name = data1.get('partner_name')
				lref = data1.get('lref')
				move_name = data1.get('move_name')
				lname = data1.get('lname')
				debit = data1.get('debit')
				credit = data1.get('credit')
				balance = data1.get('balance')
				currency_id = data1.get('currency_id')
				sheet.write(row+inner_index,col,date)
				sheet.write(row+inner_index,col+1,lcode)
				sheet.write(row+inner_index,col+2,partner_name)
				sheet.write(row+inner_index,col+3,lref)
				sheet.write(row+inner_index,col+4,move_name)
				sheet.write(row+inner_index,col+5,lname)
				sheet.write(row+inner_index,col+6,debit)
				sheet.write(row+inner_index,col+7,credit)
				sheet.write(row+inner_index,col+8,balance)
				sheet.write(row+inner_index,col+9,name)
			row = row + len(data.get('move_lines')) + 1
		fp = StringIO()
		workbook.save(fp)
		excel_file = base64.encodestring(fp.getvalue())
		self.excel_file = excel_file
		self.file_name =filename
		fp.close()
		ir_model_data = self.env['ir.model.data']
		compose_form_id = ir_model_data.get_object_reference('account', 'account_report_general_ledger_view')[1]
		return {            
		'type': 'ir.actions.act_window',            
		'view_type': 'form',            
		'view_mode': 'form',            
		'res_model': 'account.report.general.ledger',            
		'views': [(compose_form_id, 'form')], 
		'res_id': self.id,           
		'view_id': compose_form_id,            
		'target': 'new',            
		}
	