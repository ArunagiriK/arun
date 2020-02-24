# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _,tools
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from itertools import groupby
import operator
import pandas as pd
from datetime import datetime,timedelta



class DayReportWiz(models.TransientModel):
	_name = "od.day.report.wiz"
	_description = 'Day Report Wiz' 
	date_from = fields.Date('Date From',required=True)
	date_to = fields.Date('Date To',required=True,default=fields.Date.context_today)
	html_body = fields.Html(string="Body")
	html_from = fields.Html(string="From")
	html_to = fields.Html(string="To")
	html_cc = fields.Html(string="CC")

	def od_wiz_send_mail(self,template,data):
		ir_model_data = self.env['ir.model.data']
		mail_obj = self.env['mail.template']
		template_id = ir_model_data.get_object_reference('odx_despatch_v12', template)[1]
		template = mail_obj.browse(template_id)
		user = self.env.user
		context = self.env.context
		ctx  = context.copy()
		ctx['data'] =data 
		template.with_context(ctx).send_mail(user.id,force_send=True)
		return True
	
	
	def days_between(self,d1, d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1), "%Y-%m-%d")
		d2 = datetime.strptime(str(d2), "%Y-%m-%d")
		return abs((d2 - d1).days)+1


	def get_salesman_target(self,sales_area,sales_person):
		area_obj = self.env['orchid.partner.area'].search([('name','=',sales_area)])
		sales_person_obj = self.env['res.users'].search([('name','=',sales_person)]) 
		salesman = self.env['orchid.partner.area.salesman.line'].search([('od_salesman_id','=',sales_person_obj.id),('area_line_id','=',area_obj.id)])
		target = 0
		if salesman.id:
			return salesman.od_target
		return target


	def get_division_target(self,group):
		group_obj = self.env['orchid.partner.group'].search([('name','=',group)])
		target = 0
		if group_obj.id:
			return group_obj.od_target
#         category_id = self.env['orchid.category'].search([('name','=',category)]).id
#         target_master =self.env['orchid.division.target'].search([('division_id','=',division_id),('category_id','=',category_id)])
#         target = target_master.sale_target
		return target
		
	
	
	@api.multi
	def send_report(self):
		date_from,date_to = self.date_from,self.date_to
		no_of_days = self.days_between(date_from, date_to)
		company_currency = self.env.user.company_id.currency_id
		division_obj = self.env['orchid.account.cost.center']
		category_obj = self.env['orchid.category']
		group_obj = self.env['orchid.partner.group']
		invoice = self.env['account.invoice']
		total_sales = []
		invoice_ids = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',date_to),('state','not in',('cancel','draft')),('type','=','out_invoice')])
		sales = [{'date_invoice':inv.date_invoice,'number':inv.number,'partner':inv.partner_id.name,
				 'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'sale_target':inv.partner_id and inv.partner_id.od_sale_target or 0.0,
				 'amount':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency),'user':inv.user_id.name,'type':inv.type} for inv in invoice_ids]

		# print sales,'SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSs'

		ret_invoice_ids = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',date_to),('state','not in',('cancel','draft')),('type','=','out_refund')])
		sales_return = [{'date_invoice':inv.date_invoice,'number':inv.number,'partner':inv.partner_id.name,
				 'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'sales_return':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency),'user':inv.user_id.name,'type':inv.type} for inv in ret_invoice_ids]
		

		day_invoice_ids = invoice.search([('date_invoice','=',date_to),('state','not in',('cancel','draft')),('type','=','out_invoice')])
		day_sales =  [{'date_invoice':datetime.strptime(inv.date_invoice,'%Y-%m-%d').strftime("%d-%m-%Y"),'number':inv.number,'partner':inv.partner_id.name,
				 'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'day_sale':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) or 0.0,'user':inv.user_id.name,'type':inv.type} for inv in day_invoice_ids]
		
		
		day_return_ids = invoice.search([('date_invoice','=',date_to),('state','not in',('cancel','draft')),('type','=','out_refund')])
		day_return =  [{'date_invoice':datetime.strptime(inv.date_invoice,'%Y-%m-%d').strftime("%d-%m-%Y"),'number':inv.number,'partner':inv.partner_id.name,
				 'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'day_return':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) or 0.0,'user':inv.user_id.name,'type':inv.type} for inv in day_return_ids]


		# Category wise Total
		cat_ttl = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',date_to),('state','not in',('cancel','draft')),('type','=','out_invoice')])
		cat_dict =  [{'category':inv.od_category_id and inv.od_category_id.name  or '',
						'amount':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) or 0.0 } for inv in cat_ttl ]
		

		cat_df = pd.DataFrame(cat_dict)
		cat_grp = cat_df.groupby(['category']).sum()

		

		
		
		day_sale_value = sum([inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) for inv in day_invoice_ids ])
		day_return_value = sum([inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) for inv in day_return_ids ])
		day_sale_value = day_sale_value - day_return_value
		cur_date = datetime.strptime(date_to, "%Y-%m-%d") 
		prev_date =cur_date + timedelta(days=-1) 
		prev_date = prev_date.strftime('%Y-%m-%d')
#         prev_invoice_ids = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',prev_date),('state','not in',('cancel','draft')),('type','=','out_invoice')])      
#         prev_day_sales = [{'date_invoice':inv.date_invoice,'number':inv.number,'partner':inv.partner_id.name,
#                  'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
#                  'category':inv.partner_id and inv.partner_id.od_category_id and inv.partner_id.od_category_id.name or '',
#                  'area':inv.partner_id and inv.partner_id.od_area_id and inv.partner_id.od_area_id.name or '',
#                  'sales_upto':inv.amount_untaxed,'user':inv.user_id.name,'type':inv.type} for inv in prev_invoice_ids]
#         prev_day_sale_value = sum([inv.amount_untaxed for inv in prev_invoice_ids ])
#         total_sale_value = day_sale_value + prev_day_sale_value - day_return_value
#         per_day_sale = total_sale_value/no_of_days
		
		#division Categroy wise
		
		sales_df = pd.DataFrame(sales)
		# print "sales_dfffffffffffffffffffffffffff\n",sales_df
		sales_return_df = pd.DataFrame(sales_return)
		day_sale_grp = False
		# print day_sales,'KKKKKKKKKKKKKKKKKKKKKKK'
		result_cat = cat_grp

		

		if day_sales:
			day_sale_df = pd.DataFrame(day_sales)
			cat_day_sale_df = day_sale_df.groupby(['category']).sum()
			day_sale_grp = day_sale_df.groupby(['group','category','division']).sum()
			result_cat =pd.concat([result_cat,cat_day_sale_df], axis=1)
		# print 'resultttttttt_cattttttttttttt',result_cat
		sales_grp = sales_df.groupby(['group','category','division']).sum()
		# print "sales_grpppppppppppppppppppppppppppppppp",sales_grp
		result = sales_grp

		# print 'total_salestotal_salestotal_sales',total_sales

		# if total_sales:
		# 	total_sales_df = pd.DataFrame(total_sales)
		# 	total_sales_grp_df = total_sales_df.groupby(['category']).sum()
		# 	result =pd.concat([result, total_sales_grp_df], axis=1)
		# 	# print result

		
		if  day_return:
			day_return_df = pd.DataFrame(day_return)
			cat_day_return_df = day_return_df.groupby(['category']).sum()
			day_return_grp = day_return_df.groupby(['group','category','division']).sum()
			result =pd.concat([result, day_return_grp], axis=1)
			result_cat =pd.concat([result_cat,cat_day_return_df], axis=1)
			# print 'resultttttttt_cattttttttttttt222222222',result_cat
			
		if sales_return:
			sales_return_df = pd.DataFrame(sales_return)
			cat_sale_return_df = sales_return_df.groupby(['category']).sum()
			sales_ret_grp_df = sales_return_df.groupby(['group','category','division']).sum()
#             result = sales_grp.join(sales_ret_grp_df)
			result =pd.concat([result, sales_ret_grp_df], axis=1)
			# result_cat =pd.concat([result_cat,sales_ret_grp_df], axis=1)
			result_cat =pd.concat([result_cat,cat_sale_return_df], axis=1)
			# print 'resultttttttt_cattttttttttttt3333333333',result_cat

			

		if day_sales:
#             result = result.join(day_sale_grp)
			result =pd.concat([result, day_sale_grp], axis=1)
			
		# print "resultttttttttttt_cattttttttttttttttttttt",result_cat
		if sales_return:
			# print result
			result['net_sales'] = result['amount'] - result['sales_return']
			result_cat['net_sales'] = result_cat['amount'] - result_cat['sales_return']
		else:
			result['net_sales'] = result['amount']
			result_cat['net_sales'] = result_cat['amount']
		result['total_sales'] = result['net_sales']
		result_cat['total_sales'] = result_cat['net_sales']
		# print "resultttttttttabvvvvvvvvvvvvvvvvvvresssssssss",result
		result=result.fillna(0)
		result_cat = result_cat.fillna(0)
		# print "result_cattttttttttttttt_aftr_fillna",result_cat
		# print "result division wise>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",result
		result_xcat = []
		for index,row in result_cat.iterrows():
			# category = row.name[0]
			day_sale = row.get('day_sale',0.0) - row.get('day_return',0.0)
			amount = row.amount.item()
			x_sales_return=row.get('sales_return',0.0)
			net_sales = amount - x_sales_return
			# print "netttttttttttttttttttttt_salesssssssssssssssssssssss",net_sales
			# print "rowssssssssssssssssssssssssssssssssss result_xcatssssssssss",row
			result_xcat.append({'amount':row.amount.item(),'category':row.name,'day_sale':day_sale,'sales_return':row.get('sales_return',0.0),'net_sales':net_sales})
		# print 'result_xcatttttttttttttttttttt',result_xcat






		

		cat_total_key = []
		cat_total = {}

		result_x = []
		for index, row in result.iterrows():
			# print "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",row
			sale_ach =100
			bal_req = 0.0
			division = row.name[2]
			category = row.name[1]
			group = row.name[0]
			div_target = self.get_division_target(group)
			
			if div_target :
				sale_ach = (row.net_sales.item() /div_target) * 100
			ex_sht = row.net_sales.item() - div_target
			if ex_sht <0:
				bal_req = ex_sht /no_of_days
			
			seq = category_obj.search([('name','=',row.name[1])]) and category_obj.search([('name','=',row.name[1])]).code or 10
			grp_seq = group_obj.search([('name','=',row.name[0])]) and group_obj.search([('name','=',row.name[0])]).od_code or 13
			# print 'seqqqqqqqqqqqqqqqqqqqqqqqqqq',seq
			amount = row.amount.item()
			x_sales_return=row.get('sales_return',0.0)
			net_sales = amount - x_sales_return
			day_sale = row.get('day_sale',0.0) - row.get('day_return',0.0)
			result_x.append({'amount':row.amount.item(),'sales_return':row.get('sales_return',0.0),'net_sales':net_sales,'day_sale':day_sale,
							'total_sales':net_sales,'group':row.name[0],'category':row.name[1],'division':row.name[2],'divsion_target':div_target,
							'sale_target':row.sale_target.item(),'sale_ach':sale_ach,'bal_req':abs(bal_req),'ex_sht':ex_sht,
							'seq':int(seq),'od_total_col':0,'grp_seq':int(grp_seq),
							})
			#Total
			if str(category)+' Total' in cat_total_key:
				tsales_return = cat_total[category]['sales_return'] + row.get('sales_return',0.0)
				tnet_sales = cat_total[category]['net_sales'] + net_sales
				tamount = cat_total[category]['amount'] + row.amount.item()
				tday_sale = cat_total[category]['day_sale'] + day_sale
				cat_total[category] = {
					'amount':tamount,
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
					'grp_seq':int(grp_seq),
				}
			else:
				cat_total_key.append(str(category)+' Total')
				tsales_return = row.get('sales_return',0.0)
				tnet_sales = net_sales
				tamount = row.amount.item()
				tday_sale = day_sale
				cat_total[category] = {
					'amount':tamount,
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
					'grp_seq':int(grp_seq),
				}
		

			
		amount=sal_return =net_sales=day_sale  = 0.0  
		cat_amount = 0.0

		for data in result_x:
			amount += data.get('amount',0.0)
			sal_return += data.get('sales_return',0.0)
			net_sales += data.get('net_sales',0.0)
			day_sale += data.get('day_sale',0.0)
			data['amount'] = "{0:,.2f}".format(data['amount'])
			data['sales_return'] = "{0:,.2f}".format(data['sales_return'])
			data['net_sales'] = "{0:,.2f}".format(data['net_sales'])
			data['day_sale'] = "{0:,.2f}".format(data['day_sale'])
			data['total_sales'] = "{0:,.2f}".format(data['total_sales'])
			data['sale_target'] = "{0:,.2f}".format(data['sale_target'])
			data['sale_ach'] = "{0:,.2f}".format(data['sale_ach']) + '%'
			data['bal_req'] = "{0:,.2f}".format(data['bal_req'])
			data['ex_sht'] = "{0:,.2f}".format(data['ex_sht'])
			
		result_x_sum = {'amount':"{0:,.2f}".format(amount),'sales_return':"{0:,.2f}".format(sal_return),
						'net_sales':"{0:,.2f}".format(net_sales),'day_sale':"{0:,.2f}".format(day_sale)}
		
		for key,value in cat_total.iteritems():
			if key == '':
				value['category'] = 'Unknown Total'
			result_x.append(value)
		# print "resssssssssssssssssssssssssssssssssssssssssssssxxxxxxxxxxxxxxxxxxxxxx",result_x





		# print 'resultxsummmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm',result_x_sum						
		#Salesmanwise Wise
		day_sale_user = False
		
			
		sales_user = sales_df.groupby(['user','category','area']).sum()
		result = sales_user
	   
			
		
		
		if sales_return:
			sales_ret_user_df = sales_return_df.groupby(['user','category','area']).sum()
			# print "sales_ret_user_dfffffffffffffffffffffffffffffffffffff",sales_ret_user_df
#             result = sales_user.join(sales_ret_user_df)
			result =pd.concat([result, sales_ret_user_df], axis=1)
		if day_sales:
#             result = result.join(day_sale_user)
			day_sale_user = day_sale_df.groupby(['user','category','area']).sum()
			result =pd.concat([result, day_sale_user], axis=1)
		if day_return:
			day_ret_user = day_return_df.groupby(['user','category','area']).sum()
			result =pd.concat([result, day_ret_user], axis=1)
		if sales_return:
			result['net_sales'] = result['amount'] - result['sales_return']
		if not sales_return:
			result['net_sales'] = result['amount']
		result['total_sales'] = result['net_sales']
		result=result.fillna(0)
		# print 'resulttttttsalemaaaaannnnnnnnnnnnnnnnnwissssssssssssss',results
		cat_total_key = []
		cat_total = {}
		result_y = []
		for index, row in result.iterrows():
			category = row.name[1]
			sale_ach =100
			bal_req = 0.0
			if row.sale_target :
				sale_ach = (row.net_sales.item() /row.sale_target.item()) * 100
			ex_sht = row.net_sales.item() - row.sale_target.item()
			if ex_sht <0:
				bal_req = ex_sht /no_of_days

			salesman_target = self.get_salesman_target(row.name[2],row.name[0])
			amount = row.amount.item()
			x_sales_return=row.get('sales_return',0.0)
			net_sales = amount - x_sales_return
			day_sale = row.get('day_sale',0.0) - row.get('day_return',0.0)
			seq = category_obj.search([('name','=',row.name[1])]) and category_obj.search([('name','=',row.name[1])]).code or 10

			result_y.append({'amount':row.amount.item(),'sales_return':row.get('sales_return',0.0),'net_sales':net_sales,'day_sale':day_sale,
							'total_sales':net_sales,'user':row.name[0],'category':row.name[1],'area':row.name[2],
							'sale_target':salesman_target,'sale_ach':sale_ach,'bal_req':abs(bal_req),'ex_sht':ex_sht,
							'seq':int(seq),'od_total_col':0,
							})
			# print "rssssssssssssssssssssss",result_y
			#Total
			if str(category)+' Total' in cat_total_key:
				tsales_return = cat_total[category]['sales_return'] + row.get('sales_return',0.0)
				tnet_sales = cat_total[category]['net_sales'] + net_sales
				tamount = cat_total[category]['amount'] + row.amount.item()
				tday_sale = cat_total[category]['day_sale'] + day_sale
				cat_total[category] = {
					'amount':tamount,
					'user':row.name[0],
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'area':row.name[2],
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
				}
			else:
				cat_total_key.append(str(category)+' Total')
				tsales_return = row.get('sales_return',0.0)
				tnet_sales = net_sales
				tamount = row.amount.item()
				tday_sale = day_sale
				cat_total[category] = {
					'amount':tamount,
					'user':row.name[0],
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'area':row.name[2],
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
				}
		
	
		amount=sal_return =net_sales = day_sale  = 0.0  
		for data in result_y:
			amount += data.get('amount',0.0)
			sal_return += data.get('sales_return',0.0)
			net_sales += data.get('net_sales',0.0)
			day_sale += data.get('day_sale',0.0)
			data['amount'] = "{0:,.2f}".format(data['amount'])
			data['sales_return'] = "{0:,.2f}".format(data['sales_return'])
			data['net_sales'] = "{0:,.2f}".format(data['net_sales'])
			data['day_sale'] = "{0:,.2f}".format(data['day_sale'])
			data['total_sales'] = "{0:,.2f}".format(data['total_sales'])
			data['sale_target'] = "{0:,.2f}".format(data['sale_target'])
			data['sale_ach'] = "{0:,.2f}".format(data['sale_ach']) + '%'
			data['bal_req'] = "{0:,.2f}".format(data['bal_req'])
			data['ex_sht'] = "{0:,.2f}".format(data['ex_sht'])
		result_y_sum = {'amount':"{0:,.2f}".format(amount),
						'day_sale':day_sale,'sales_return':"{0:,.2f}".format(sal_return),'net_sales':"{0:,.2f}".format(net_sales)}
		for key,value in cat_total.iteritems():
			if key == '':
				value['category'] = 'Unknown Total'
			result_y.append(value)
		# print "resssssssssssssssyyyyyyyyyyyyyyyyy",result_y	

		#change the amounts for correctio
		total_sale_value = net_sales
		prev_day_sale_value = net_sales -day_sale_value
		per_day_sale = total_sale_value/no_of_days
		##############################
		# day_sales =sorted(day_sales, key=lambda k: k['user']) 
		# day_return =sorted(day_return, key=lambda k: k['user'])
		# result_y = sorted(result_y, key=lambda k: k['user'])
		
		for val in day_sales:
			val['day_sale'] =  "{0:,.2f}".format(val['day_sale'])
		
		for val in day_return:
			val['day_return'] =  "{0:,.2f}".format(val['day_return'])
		
		date_to = datetime.strptime(date_to, "%Y-%m-%d")
		prev_date = datetime.strptime(prev_date, "%Y-%m-%d")
		result_x = sorted(result_x, key=lambda k: (k['seq'],k['grp_seq']))
		result_y = sorted(result_y, key=lambda k: (k['seq'],k['area']))
		# result_y_sort = sorted(result_y, key=lambda k: k['user'])
		day_sales = sorted(day_sales, key=lambda k: k['number'])
		day_return =sorted(day_return, key=lambda k: k['number'])

		data = {
			'date_to':date_to.strftime("%d.%m.%Y"),
			'days':no_of_days,
			'prev_date':prev_date.strftime("%d.%m.%Y"),
			'day_sale_value':"{0:,.2f}".format(day_sale_value),
			'sales_per_day':"{0:,.2f}".format(per_day_sale),
			'total_sale_value':"{0:,.2f}".format(total_sale_value),
			'prev_day_sale_value':"{0:,.2f}".format(prev_day_sale_value),
			'group_wise':result_x,
			'group_wise_sum':result_x_sum,
			'cat_wise_sum':result_xcat,
			'user_wise':result_y,
			'user_wise_sum':result_y_sum,
			'day_sale':day_sales,
			'day_return':day_return,
			'day_return_value':"{0:,.2f}".format(day_return_value),
			}
		self.od_wiz_send_mail('email_bfly_daily_report', data)
		
		
#             
#             summary.append({'Area':area,'Quotation':quotation,'SaleOrder':sale_order,'Delivered':deliverd,'Invoiced':invoiced})
#         self.od_wiz_send_mail('email_order_status_summary', data, summary)
	@api.multi
	def show_template(self):
		date_from,date_to = self.date_from,self.date_to
		no_of_days = self.days_between(date_from, date_to)
		company_currency = self.env.user.company_id.currency_id
		# division_obj = self.env['orchid.account.cost.center']
		category_obj = self.env['orchid.category']
		group_obj = self.env['orchid.partner.group']
		invoice = self.env['account.invoice']
		total_sales = []
		invoice_ids = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',date_to),('state','not in',('cancel','draft')),('type','=','out_invoice')])
		sales = [{'date_invoice':inv.date_invoice,'number':inv.number,'partner':inv.partner_id.name,
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'sale_target':inv.partner_id and inv.partner_id.od_sale_target or 0.0,
				 'amount':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency),'user':inv.user_id.name,'type':inv.type} for inv in invoice_ids]

		# print sales,'SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSs'

		ret_invoice_ids = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',date_to),('state','not in',('cancel','draft')),('type','=','out_refund')])
		sales_return = [{'date_invoice':inv.date_invoice,'number':inv.number,'partner':inv.partner_id.name,
				 'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'sales_return':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency),'user':inv.user_id.name,'type':inv.type} for inv in ret_invoice_ids]
		

		day_invoice_ids = invoice.search([('date_invoice','=',date_to),('state','not in',('cancel','draft')),('type','=','out_invoice')])
		day_sales =  [{'date_invoice':datetime.strptime(str(inv.date_invoice),'%Y-%m-%d').strftime("%d-%m-%Y"),'number':inv.number,'partner':inv.partner_id.name,
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'day_sale':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) or 0.0,'user':inv.user_id.name,'type':inv.type} for inv in day_invoice_ids]
		
		
		day_return_ids = invoice.search([('date_invoice','=',date_to),('state','not in',('cancel','draft')),('type','=','out_refund')])
		day_return =  [{'date_invoice':datetime.strptime(str(inv.date_invoice),'%Y-%m-%d').strftime("%d-%m-%Y"),'number':inv.number,'partner':inv.partner_id.name,
				 'category':inv.od_category_id and inv.od_category_id.name or '',
				 'area':inv.od_area_id and inv.od_area_id.name or '',
				 'group':inv.od_group_id and inv.od_group_id.name  or '',
				 'day_return':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) or 0.0,'user':inv.user_id.name,'type':inv.type} for inv in day_return_ids]


		# Category wise Total
		cat_ttl = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',date_to),('state','not in',('cancel','draft')),('type','=','out_invoice')])
		cat_dict =  [{'category':inv.od_category_id and inv.od_category_id.name  or '',
						'amount':inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) or 0.0 } for inv in cat_ttl ]
		

		cat_df = pd.DataFrame(cat_dict)
		cat_grp = cat_df.groupby(['category']).sum()

		

		
		
		day_sale_value = sum([inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) for inv in day_invoice_ids ])
		day_return_value = sum([inv.currency_id.with_context(date=inv.date_invoice).compute(inv.amount_untaxed,company_currency) for inv in day_return_ids ])
		day_sale_value = day_sale_value - day_return_value
		cur_date = datetime.strptime(str(date_to), "%Y-%m-%d")
		prev_date =cur_date + timedelta(days=-1) 
		prev_date = prev_date.strftime('%Y-%m-%d')
#         prev_invoice_ids = invoice.search([('date_invoice','>=',date_from),('date_invoice','<=',prev_date),('state','not in',('cancel','draft')),('type','=','out_invoice')])      
#         prev_day_sales = [{'date_invoice':inv.date_invoice,'number':inv.number,'partner':inv.partner_id.name,
#                  'division':inv.partner_id and inv.partner_id.od_division_id and inv.partner_id.od_division_id.name or '',
#                  'category':inv.partner_id and inv.partner_id.od_category_id and inv.partner_id.od_category_id.name or '',
#                  'area':inv.partner_id and inv.partner_id.od_area_id and inv.partner_id.od_area_id.name or '',
#                  'sales_upto':inv.amount_untaxed,'user':inv.user_id.name,'type':inv.type} for inv in prev_invoice_ids]
#         prev_day_sale_value = sum([inv.amount_untaxed for inv in prev_invoice_ids ])
#         total_sale_value = day_sale_value + prev_day_sale_value - day_return_value
#         per_day_sale = total_sale_value/no_of_days
		
		#division Categroy wise
		
		sales_df = pd.DataFrame(sales)
		# print "sales_dfffffffffffffffffffffffffff\n",sales_df
		sales_return_df = pd.DataFrame(sales_return)
		day_sale_grp = False
		# print day_sales,'KKKKKKKKKKKKKKKKKKKKKKK'
		result_cat = cat_grp

		

		if day_sales:
			day_sale_df = pd.DataFrame(day_sales)
			cat_day_sale_df = day_sale_df.groupby(['category']).sum()
			day_sale_grp = day_sale_df.groupby(['group','category']).sum()
			result_cat =pd.concat([result_cat,cat_day_sale_df], axis=1)
		# print 'resultttttttt_cattttttttttttt',result_cat
		sales_grp = sales_df.groupby(['group','category']).sum()
		# print "sales_grpppppppppppppppppppppppppppppppp",sales_grp
		result = sales_grp

		# print 'total_salestotal_salestotal_sales',total_sales

		# if total_sales:
		# 	total_sales_df = pd.DataFrame(total_sales)
		# 	total_sales_grp_df = total_sales_df.groupby(['category']).sum()
		# 	result =pd.concat([result, total_sales_grp_df], axis=1)
		# 	# print result

		
		if  day_return:
			day_return_df = pd.DataFrame(day_return)
			cat_day_return_df = day_return_df.groupby(['category']).sum()
			day_return_grp = day_return_df.groupby(['group','category','division']).sum()
			result =pd.concat([result, day_return_grp], axis=1)
			result_cat =pd.concat([result_cat,cat_day_return_df], axis=1)
			# print 'resultttttttt_cattttttttttttt222222222',result_cat
			
		if sales_return:
			sales_return_df = pd.DataFrame(sales_return)
			cat_sale_return_df = sales_return_df.groupby(['category']).sum()
			sales_ret_grp_df = sales_return_df.groupby(['group','category','division']).sum()
#             result = sales_grp.join(sales_ret_grp_df)
			result =pd.concat([result, sales_ret_grp_df], axis=1)
			# result_cat =pd.concat([result_cat,sales_ret_grp_df], axis=1)
			result_cat =pd.concat([result_cat,cat_sale_return_df], axis=1)
			# print 'resultttttttt_cattttttttttttt3333333333',result_cat

			

		if day_sales:
#             result = result.join(day_sale_grp)
			result =pd.concat([result, day_sale_grp], axis=1)
			
		# print "resultttttttttttt_cattttttttttttttttttttt",result_cat
		if sales_return:
			# print result
			result['net_sales'] = result['amount'] - result['sales_return']
			result_cat['net_sales'] = result_cat['amount'] - result_cat['sales_return']
		else:
			result['net_sales'] = result['amount']
			result_cat['net_sales'] = result_cat['amount']
		result['total_sales'] = result['net_sales']
		result_cat['total_sales'] = result_cat['net_sales']
		# print "resultttttttttabvvvvvvvvvvvvvvvvvvresssssssss",result
		result=result.fillna(0)
		result_cat = result_cat.fillna(0)
		# print "result_cattttttttttttttt_aftr_fillna",result_cat
		# print "result division wise>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",result
		result_xcat = []
		for index,row in result_cat.iterrows():
			# category = row.name[0]
			day_sale = row.get('day_sale',0.0) - row.get('day_return',0.0)
			amount = row.amount.item()
			x_sales_return=row.get('sales_return',0.0)
			net_sales = amount - x_sales_return
			# print "netttttttttttttttttttttt_salesssssssssssssssssssssss",net_sales
			# print "rowssssssssssssssssssssssssssssssssss result_xcatssssssssss",row
			result_xcat.append({'amount':row.amount.item(),'category':row.name,'day_sale':day_sale,'sales_return':row.get('sales_return',0.0),'net_sales':net_sales})
		# print 'result_xcatttttttttttttttttttt',result_xcat






		

		cat_total_key = []
		cat_total = {}

		result_x = []
		for index, row in result.iterrows():
			# print "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",row
			sale_ach =100
			bal_req = 0.0
			category = row.name[1]
			group = row.name[0]
			div_target = self.get_division_target(group)
			
			if div_target :
				sale_ach = (row.net_sales.item() /div_target) * 100
			ex_sht = row.net_sales.item() - div_target
			if ex_sht <0:
				bal_req = ex_sht /no_of_days
			
			seq = category_obj.search([('name','=',row.name[1])]) and category_obj.search([('name','=',row.name[1])]).code or 10
			grp_seq = group_obj.search([('name','=',row.name[0])]) and group_obj.search([('name','=',row.name[0])]).od_code or 13
			# print 'seqqqqqqqqqqqqqqqqqqqqqqqqqq',seq
			amount = row.amount.item()
			x_sales_return=row.get('sales_return',0.0)
			net_sales = amount - x_sales_return
			day_sale = row.get('day_sale',0.0) - row.get('day_return',0.0)
			result_x.append({'amount':row.amount.item(),'sales_return':row.get('sales_return',0.0),'net_sales':net_sales,'day_sale':day_sale,
							'total_sales':net_sales,'group':row.name[0],'category':row.name[1],'division':row.name[2],'divsion_target':div_target,
							'sale_target':row.sale_target.item(),'sale_ach':sale_ach,'bal_req':abs(bal_req),'ex_sht':ex_sht,
							'seq':int(seq),'od_total_col':0,'grp_seq':int(grp_seq),
							})
			#Total
			if str(category)+' Total' in cat_total_key:
				tsales_return = cat_total[category]['sales_return'] + row.get('sales_return',0.0)
				tnet_sales = cat_total[category]['net_sales'] + net_sales
				tamount = cat_total[category]['amount'] + row.amount.item()
				tday_sale = cat_total[category]['day_sale'] + day_sale
				cat_total[category] = {
					'amount':tamount,
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
					'grp_seq':int(grp_seq),
				}
			else:
				cat_total_key.append(str(category)+' Total')
				tsales_return = row.get('sales_return',0.0)
				tnet_sales = net_sales
				tamount = row.amount.item()
				tday_sale = day_sale
				cat_total[category] = {
					'amount':tamount,
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
					'grp_seq':int(grp_seq),
				}
		

			
		amount=sal_return =net_sales=day_sale  = 0.0  
		cat_amount = 0.0

		for data in result_x:
			amount += data.get('amount',0.0)
			sal_return += data.get('sales_return',0.0)
			net_sales += data.get('net_sales',0.0)
			day_sale += data.get('day_sale',0.0)
			data['amount'] = "{0:,.2f}".format(data['amount'])
			data['sales_return'] = "{0:,.2f}".format(data['sales_return'])
			data['net_sales'] = "{0:,.2f}".format(data['net_sales'])
			data['day_sale'] = "{0:,.2f}".format(data['day_sale'])
			data['total_sales'] = "{0:,.2f}".format(data['total_sales'])
			data['sale_target'] = "{0:,.2f}".format(data['sale_target'])
			data['sale_ach'] = "{0:,.2f}".format(data['sale_ach']) + '%'
			data['bal_req'] = "{0:,.2f}".format(data['bal_req'])
			data['ex_sht'] = "{0:,.2f}".format(data['ex_sht'])
			
		result_x_sum = {'amount':"{0:,.2f}".format(amount),'sales_return':"{0:,.2f}".format(sal_return),
						'net_sales':"{0:,.2f}".format(net_sales),'day_sale':"{0:,.2f}".format(day_sale)}
		
		for key,value in cat_total.iteritems():
			if key == '':
				value['category'] = 'Unknown Total'
			result_x.append(value)
		# print "resssssssssssssssssssssssssssssssssssssssssssssxxxxxxxxxxxxxxxxxxxxxx",result_x





		# print 'resultxsummmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm',result_x_sum						
		#Salesmanwise Wise
		day_sale_user = False
		
			
		sales_user = sales_df.groupby(['user','category','area']).sum()
		result = sales_user
	   
			
		
		
		if sales_return:
			sales_ret_user_df = sales_return_df.groupby(['user','category','area']).sum()
			# print "sales_ret_user_dfffffffffffffffffffffffffffffffffffff",sales_ret_user_df
#             result = sales_user.join(sales_ret_user_df)
			result =pd.concat([result, sales_ret_user_df], axis=1)
		if day_sales:
#             result = result.join(day_sale_user)
			day_sale_user = day_sale_df.groupby(['user','category','area']).sum()
			result =pd.concat([result, day_sale_user], axis=1)
		if day_return:
			day_ret_user = day_return_df.groupby(['user','category','area']).sum()
			result =pd.concat([result, day_ret_user], axis=1)
		if sales_return:
			result['net_sales'] = result['amount'] - result['sales_return']
		if not sales_return:
			result['net_sales'] = result['amount']
		result['total_sales'] = result['net_sales']
		result=result.fillna(0)
		# print 'resulttttttsalemaaaaannnnnnnnnnnnnnnnnwissssssssssssss',results
		cat_total_key = []
		cat_total = {}
		result_y = []
		for index, row in result.iterrows():
			category = row.name[1]
			sale_ach =100
			bal_req = 0.0
			if row.sale_target :
				sale_ach = (row.net_sales.item() /row.sale_target.item()) * 100
			ex_sht = row.net_sales.item() - row.sale_target.item()
			if ex_sht <0:
				bal_req = ex_sht /no_of_days

			salesman_target = self.get_salesman_target(row.name[2],row.name[0])
			amount = row.amount.item()
			x_sales_return=row.get('sales_return',0.0)
			net_sales = amount - x_sales_return
			day_sale = row.get('day_sale',0.0) - row.get('day_return',0.0)
			seq = category_obj.search([('name','=',row.name[1])]) and category_obj.search([('name','=',row.name[1])]).code or 10

			result_y.append({'amount':row.amount.item(),'sales_return':row.get('sales_return',0.0),'net_sales':net_sales,'day_sale':day_sale,
							'total_sales':net_sales,'user':row.name[0],'category':row.name[1],'area':row.name[2],
							'sale_target':salesman_target,'sale_ach':sale_ach,'bal_req':abs(bal_req),'ex_sht':ex_sht,
							'seq':int(seq),'od_total_col':0,
							})
			# print "rssssssssssssssssssssss",result_y
			#Total
			if str(category)+' Total' in cat_total_key:
				tsales_return = cat_total[category]['sales_return'] + row.get('sales_return',0.0)
				tnet_sales = cat_total[category]['net_sales'] + net_sales
				tamount = cat_total[category]['amount'] + row.amount.item()
				tday_sale = cat_total[category]['day_sale'] + day_sale
				cat_total[category] = {
					'amount':tamount,
					'user':row.name[0],
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'area':row.name[2],
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
				}
			else:
				cat_total_key.append(str(category)+' Total')
				tsales_return = row.get('sales_return',0.0)
				tnet_sales = net_sales
				tamount = row.amount.item()
				tday_sale = day_sale
				cat_total[category] = {
					'amount':tamount,
					'user':row.name[0],
					'sales_return':tsales_return,
					'net_sales':tnet_sales,
					'day_sale':tday_sale,
					'total_sales':0,
					'group':'',
					'category':str(category) + ' Total',
					'area':row.name[2],
					'division':'',
					'divsion_target':div_target,
					'sale_target':row.sale_target.item(),
					'sale_ach':sale_ach,
					'bal_req':abs(bal_req),
					'ex_sht':ex_sht,
					'seq':int(seq) + 1,
					'od_total_col':1,
				}
		
	
		amount=sal_return =net_sales = day_sale  = 0.0  
		for data in result_y:
			amount += data.get('amount',0.0)
			sal_return += data.get('sales_return',0.0)
			net_sales += data.get('net_sales',0.0)
			day_sale += data.get('day_sale',0.0)
			data['amount'] = "{0:,.2f}".format(data['amount'])
			data['sales_return'] = "{0:,.2f}".format(data['sales_return'])
			data['net_sales'] = "{0:,.2f}".format(data['net_sales'])
			data['day_sale'] = "{0:,.2f}".format(data['day_sale'])
			data['total_sales'] = "{0:,.2f}".format(data['total_sales'])
			data['sale_target'] = "{0:,.2f}".format(data['sale_target'])
			data['sale_ach'] = "{0:,.2f}".format(data['sale_ach']) + '%'
			data['bal_req'] = "{0:,.2f}".format(data['bal_req'])
			data['ex_sht'] = "{0:,.2f}".format(data['ex_sht'])
		result_y_sum = {'amount':"{0:,.2f}".format(amount),
						'day_sale':day_sale,'sales_return':"{0:,.2f}".format(sal_return),'net_sales':"{0:,.2f}".format(net_sales)}
		for key,value in cat_total.iteritems():
			if key == '':
				value['category'] = 'Unknown Total'
			result_y.append(value)
		# print "resssssssssssssssyyyyyyyyyyyyyyyyy",result_y	

		#change the amounts for correctio
		total_sale_value = net_sales
		prev_day_sale_value = net_sales -day_sale_value
		per_day_sale = total_sale_value/no_of_days
		##############################
		# day_sales =sorted(day_sales, key=lambda k: k['user']) 
		# day_return =sorted(day_return, key=lambda k: k['user'])
		# result_y = sorted(result_y, key=lambda k: k['user'])
		
		for val in day_sales:
			val['day_sale'] =  "{0:,.2f}".format(val['day_sale'])
		
		for val in day_return:
			val['day_return'] =  "{0:,.2f}".format(val['day_return'])
		
		date_to = datetime.strptime(date_to, "%Y-%m-%d")
		prev_date = datetime.strptime(prev_date, "%Y-%m-%d")
		result_x = sorted(result_x, key=lambda k: (k['seq'],k['grp_seq']))
		result_y = sorted(result_y, key=lambda k: (k['seq'],k['area']))
		# result_y_sort = sorted(result_y, key=lambda k: k['user'])
		day_sales = sorted(day_sales, key=lambda k: k['number'])
		day_return =sorted(day_return, key=lambda k: k['number'])

		data = {
			'date_to':date_to.strftime("%d.%m.%Y"),
			'days':no_of_days,
			'prev_date':prev_date.strftime("%d.%m.%Y"),
			'day_sale_value':"{0:,.2f}".format(day_sale_value),
			'sales_per_day':"{0:,.2f}".format(per_day_sale),
			'total_sale_value':"{0:,.2f}".format(total_sale_value),
			'prev_day_sale_value':"{0:,.2f}".format(prev_day_sale_value),
			'group_wise':result_x,
			'group_wise_sum':result_x_sum,
			'cat_wise_sum':result_xcat,
			'user_wise':result_y,
			'user_wise_sum':result_y_sum,
			'day_sale':day_sales,
			'day_return':day_return,
			'day_return_value':"{0:,.2f}".format(day_return_value),
			}
		ir_model_data = self.env['ir.model.data']
		mail_obj = self.env['mail.template']
		template_id = ir_model_data.get_object_reference('odx_despatch_v12', 'email_bfly_daily_report')[1]
		template = mail_obj.browse(template_id)
		user = self.env.user
		context = self.env.context
		ctx  = context.copy()
		ctx['data'] =data 
		generated_field_values = template.with_context(ctx).render_template(
			getattr(template, 'body_html'), template.model, [user.id],True)
		self.html_from = user.email
		self.html_to = template.email_to
		self.html_cc = template.email_cc
		self.html_body = generated_field_values[user.id]
		return {
			'name':'Day Report Summary',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'od.day.report.wiz',
			'res_id': self.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		} 
