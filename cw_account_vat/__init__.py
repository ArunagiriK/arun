# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Codeware Computiung LLC (<http://www.codewareuae.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from . import wizard, models

from odoo import api, SUPERUSER_ID

def _auto_correct_l10n(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    CompanyObj = env['res.company']
    CountryObj = env['res.country']
    AccountTaxObj = env['account.tax']
    AccountChartTemplateObj = env['account.chart.template']
    #AccountTaxTemplateObj = env['account.tax.template']
    
    foreign_country_group = env.ref('cw_account_vat.country_group_foreign_countries', False)
    if foreign_country_group:
        foreign_countries = []
        for foreign_country in CountryObj.search([('code', '!=', 'AE')]):
            foreign_countries.append(foreign_country.id)
        if foreign_countries:
            foreign_country_group.country_ids = [(6, 0, foreign_countries)]
    
    for company in CompanyObj.search([]):
        taxes_ref = {}
        company_id = str(company.id)
        
        current_module = 'cw_account_vat'        
        country_module = 'l10n_ae'
        
        
        normal_sale_tax_temp = company_id+'_sale_tax_template'
        normal_sale_tax_ref =  '.'.join([country_module, normal_sale_tax_temp])
        normal_sale_tax = env.ref(normal_sale_tax_ref, False)
        
        
        normal_purchase_tax_temp = company_id+'_purchase_tax_template'
        normal_purchase_tax_ref =  '.'.join([country_module, normal_purchase_tax_temp])
        normal_purchase_tax = env.ref(normal_purchase_tax_ref, False)
        
        normal_sale_tax_acc_id = normal_sale_tax and normal_sale_tax.account_id or False
        normal_sale_tax_ref_acc_id = normal_sale_tax and normal_sale_tax.refund_account_id or False
        
        
        normal_pur_tax_acc_id = normal_purchase_tax and normal_purchase_tax.account_id or False
        normal_pur_tax_ref_acc_id = normal_purchase_tax and normal_purchase_tax.refund_account_id or False
        
        
        tax_temps = ['0', 'E', 'reverse']
        for tx_tmp in tax_temps:
            tax_temp = company_id+'_sale_tax_template_'+tx_tmp        
            tax_ref =  '.'.join([current_module, tax_temp])
            tax_account = env.ref(tax_ref, False)
            if not tax_account:
                if normal_sale_tax:
                    tax_template = env.ref('cw_account_vat.sale_tax_template_'+tx_tmp, False)
                    generated_tax_res = tax_template._generate_tax(company)
                    taxes_ref.update(generated_tax_res['tax_template_to_tax']) 
                    for key, value in generated_tax_res['account_dict'].items():
                        if value['refund_account_id'] or value['account_id']:
                            AccountTaxObj.browse(key).write({
                                'account_id': normal_sale_tax_acc_id and normal_sale_tax_acc_id.id or False,
                                'refund_account_id': normal_sale_tax_ref_acc_id and normal_sale_tax_ref_acc_id.id or False,
                            })
                            
            tax_temp = company_id+'_purchase_tax_template_'+tx_tmp         
            tax_ref =  '.'.join([current_module, tax_temp])
            tax_account = env.ref(tax_ref, False)
            if not tax_account:
                if normal_purchase_tax:
                    tax_template = env.ref('cw_account_vat.purchase_tax_template_'+tx_tmp, False)
                    generated_tax_res = tax_template._generate_tax(company)
                    taxes_ref.update(generated_tax_res['tax_template_to_tax']) 
                    for key, value in generated_tax_res['account_dict'].items():
                        if value['refund_account_id'] or value['account_id']:
                            AccountTaxObj.browse(key).write({
                                'account_id': normal_pur_tax_acc_id and normal_pur_tax_acc_id.id or False,
                                'refund_account_id': normal_pur_tax_ref_acc_id and normal_pur_tax_ref_acc_id.id or False,
                            })        
        
        
        vals = {'name': 'VAT 5%', 'description': 'VAT 5%', 'amount': 5}
        
        if normal_sale_tax:
            vals.update({'name': 'Output VAT 5%'})
            normal_sale_tax.write(vals)
            for tx in AccountTaxObj.search([('account_id', '=', False), ('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]):
                tx.write({'account_id': normal_sale_tax_acc_id and normal_sale_tax_acc_id.id or False})
            for tx in AccountTaxObj.search([('refund_account_id', '=', False), ('type_tax_use', '=', 'sale')]):
                tx.write({'refund_account_id': normal_sale_tax_ref_acc_id and normal_sale_tax_ref_acc_id.id or False})
            
            
        if normal_purchase_tax:
            vals.update({'name': 'Input VAT 5%'})
            normal_purchase_tax.write(vals)
            for tx in AccountTaxObj.search([('account_id', '=', False), ('type_tax_use', '=', 'purchase'), ('company_id', '=', company_id)]):
                tx.write({'account_id': normal_pur_tax_acc_id and normal_pur_tax_acc_id.id or False})
            for tx in AccountTaxObj.search([('refund_account_id', '=', False), ('type_tax_use', '=', 'purchase')]):
                tx.write({'refund_account_id': normal_pur_tax_ref_acc_id and normal_pur_tax_ref_acc_id.id or False})
                
        
        
        if normal_sale_tax and normal_purchase_tax:
            fp_temps = ['vat', 'non_vat', 'gcc_vat', 'non_gcc_vat', 'non_gcc', 'vat_des', 'non_vat_des']
            for fp_tmp in fp_temps:
                fp_temp = env.ref('cw_account_vat.fp_temp_'+fp_tmp, False)
                if fp_temp:
                    comp_fp_temp = company_id+'_fp_temp_'+fp_tmp        
                    comp_fp_temp =  '.'.join([current_module, comp_fp_temp])
                    comp_fp_temp = env.ref(comp_fp_temp, False)
                    if not comp_fp_temp:                
                        vals = {'company_id': company.id, 
                                'name': fp_temp.name, 
                                'tax_type': fp_temp.tax_type 
                            }
                        new_fp_temp = AccountChartTemplateObj.create_record_with_xmlid(company, 
                                                                                             fp_temp, 
                                                                                             'account.fiscal.position', vals)
                        for tax in fp_temp.tax_ids:  
                            tax_n = ['0', '1', '2']
                            for txn in tax_n:               
                                comp_fp_temp = company_id+'_tax_fp_temp_'+fp_tmp+'_'+txn     
                                comp_fp_temp =  '.'.join([current_module, comp_fp_temp])
                                comp_fp_temp = env.ref(comp_fp_temp, False)
                                if not comp_fp_temp: 
                                    AccountChartTemplateObj.create_record_with_xmlid(company, tax, 'account.fiscal.position.tax', {
                                        'tax_src_id': tax.tax_src_id.id,
                                        'tax_dest_id': tax.tax_dest_id.id,
                                        'position_id': new_fp_temp,
                                    })
            
            
            
            
            
            
            
                

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: