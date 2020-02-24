# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Codeware LLC
##############################################################################

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _

class ReportAccountVatReturnExport(models.AbstractModel):
    _name = 'report.cw_vat_return_report.vat_return_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_context_values(self, wizard):
        company_id = wizard.company_id.id
        company = self.env['res.company'].browse(company_id)
        to_date = wizard.to_date
        to_date1 = str(to_date)
        from_date = wizard.from_date
        from_date1 = str(from_date)
        target_move = 'posted'
        return (
            from_date1, to_date1, company.id, target_move
        )

    def account_tax_ids_with_moves(self, tax_id, aml_id):
        req = """
            SELECT account_move_line_id FROM account_move_line_account_tax_rel
            WHERE account_move_line_id = %s AND
                      account_tax_id = %s
        """
        self.env.cr.execute(
            req, (aml_id, tax_id))
        return [r[0] for r in self.env.cr.fetchall()]

    def get_target_type_list(self, move_type=None):
        if move_type == 'refund':
            return ['receivable_refund', 'payable_refund']
        elif move_type == 'regular':
            return ['receivable', 'payable', 'liquidity', 'other']
        return []

    def get_target_state_list(self, target_move="posted"):
        if target_move == 'posted':
            state = ['posted']
        elif target_move == 'all':
            state = ['posted', 'draft']
        else:
            state = []
        return state

    def get_move_line_partial_domain(self, from_date, to_date, company_id):
        return [
            ('date', '<=', to_date),
            ('date', '>=', from_date),
            ('company_id', '=', company_id)
        ]

    def compute_balance(self, wizard, aml_line, tax_id, tax_or_base='tax', move_type=None):
        domain = self.get_move_lines_domain(wizard, aml_line, tax_id,
            tax_or_base=tax_or_base, move_type=move_type)
        balance = self.env['account.move.line']. \
            read_group(domain, ['balance'], [])[0]['balance']
        return balance and -balance or 0

    def compute_adjustment(self, wizard, aml_line, tax_id, tax_or_base='tax', move_type=None):
        domain = self.get_move_lines_domain(wizard, aml_line, tax_id,
            tax_or_base=tax_or_base, move_type=move_type)
        domain.append(('refund_invoice_id.move_id.date', '<', wizard.from_date))
        balance = self.env['account.move.line']. \
            read_group(domain, ['balance'], [])[0]['balance']
        return balance and -balance or 0


    def get_balance_domain(self, aml_line, tax_id, state_list, type_list):
        if aml_line:
            domain = [
            ('move_id.state', 'in', state_list),
            ('tax_line_id', '=', tax_id),
            ('tax_exigible', '=', True)
            ]
            if type_list:
                domain.append(('move_id.move_type', 'in', type_list))
        else:
            domain = []
        return domain

    def get_base_balance_domain(self, aml_line, tax_id, state_list, type_list):
        if aml_line:
            domain = [
            ('move_id.state', 'in', state_list),
            ('tax_ids', 'in', tax_id),
            ('tax_exigible', '=', True)
            ]
            if type_list:
                domain.append(('move_id.move_type', 'in', type_list))
        else:
            domain = []
        return domain

    def get_move_lines_domain(self, wizard, aml_line, tax_id, tax_or_base='tax', move_type=None):
        from_date, to_date, company_id, target_move = self.get_context_values(wizard)
        state_list = self.get_target_state_list(target_move)
        type_list = self.get_target_type_list(move_type)
        domain = self.get_move_line_partial_domain(
             from_date, to_date, company_id)
        balance_domain = []
        if tax_or_base == 'tax':
            balance_domain = self.get_balance_domain(aml_line, tax_id, state_list, type_list)
        elif tax_or_base == 'base':
            balance_domain = self.get_base_balance_domain(aml_line, tax_id,
                state_list, type_list)
        if balance_domain:
            domain.extend(balance_domain)
        return domain


    def get_tax_accounts(self, company_id, type_tax_use=False):
        domain = [('company_id', '=', company_id)]
        if type_tax_use:
            domain.append(('type_tax_use', '=', type_tax_use))
        tax_accounts = self.env['account.tax'].search(domain)
        return tax_accounts
    
    def get_tax_groups(self):
        tax_groups = self.env['account.tax.group'].search([])
        return tax_groups    

    def get_sale_data(self, wizard):
        acc_tax_sale = self.get_tax_accounts(wizard.company_id.id, type_tax_use='sale')
        aml_obj = self.env['account.move.line']
        res = {}
        for sale_tax in acc_tax_sale:
            acc_move_sale_lines = aml_obj.search([('date', '>=', wizard.from_date ),
                                                    ('date', '<=', wizard.to_date),
                                                    ('company_id', '=', wizard.company_id.id)])
            for acc_move_sale in acc_move_sale_lines:
                ids_with_moves = self.account_tax_ids_with_moves(sale_tax.id, acc_move_sale.id)
                for move_line_id in ids_with_moves:
                    aml_sale_line = aml_obj.search([('id', '=', move_line_id)])
                    balance_regular = self.compute_balance(wizard, aml_sale_line, sale_tax.id,
                                                    tax_or_base='tax', move_type='regular')
                    base_balance_regular = self.compute_balance(wizard, aml_sale_line, sale_tax.id,
                                                             tax_or_base='base', move_type='regular')
                    balance_refund = self.compute_balance(wizard, aml_sale_line, sale_tax.id,
                                                     tax_or_base='tax', move_type='refund')
                    balance_refund_adjustment = self.compute_adjustment(wizard, aml_sale_line, sale_tax.id,
                                                          tax_or_base='tax', move_type='refund')
                    base_balance_refund = self.compute_balance(wizard, aml_sale_line, sale_tax.id,
                                                           tax_or_base='base', move_type='refund')
                    base_balance = (base_balance_regular + base_balance_refund)
                    balance = balance_regular + balance_refund - balance_refund_adjustment
                    res[sale_tax.tax_group_id] = res.get(sale_tax.tax_group_id, {})
                    res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id] = res[sale_tax.tax_group_id].get(aml_sale_line.partner_place_supply_country_id, {})
                    res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id][aml_sale_line.partner_place_supply_state_id] = res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id].get(aml_sale_line.partner_place_supply_state_id, {})
                    res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id][aml_sale_line.partner_place_supply_state_id][sale_tax] = res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id][aml_sale_line.partner_place_supply_state_id].get(sale_tax, {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0})
                    res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id][aml_sale_line.partner_place_supply_state_id][sale_tax]['balance'] += balance
                    res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id][aml_sale_line.partner_place_supply_state_id][sale_tax]['base_balance'] += base_balance
                    res[sale_tax.tax_group_id][aml_sale_line.partner_place_supply_country_id][aml_sale_line.partner_place_supply_state_id][sale_tax]['adjustment'] += balance_refund_adjustment
        return res

    def get_purchase_data(self, wizard):
        acc_tax_purchase = self.get_tax_accounts(wizard.company_id.id, type_tax_use='purchase')
        aml_obj = self.env['account.move.line']
        #res = {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0} 
        res = {}    
        for pur_tax in acc_tax_purchase:
            acc_move_purchase_lines = aml_obj.search([('date', '>=', wizard.from_date),
                                                        ('date', '<=', wizard.to_date),
                                                        ('company_id', '=', wizard.company_id.id)])
            for acc_move_purchase in acc_move_purchase_lines:
                ids_with_moves = self.account_tax_ids_with_moves(pur_tax.id, acc_move_purchase.id)
                for move_line_id in ids_with_moves:
                    aml_purchase_line = aml_obj.search([('id', '=', move_line_id)])
                    balance_regular = self.compute_balance(wizard, aml_purchase_line, pur_tax.id,
                                                           tax_or_base='tax', move_type='regular')
                    base_balance_regular = self.compute_balance(wizard, aml_purchase_line, pur_tax.id,
                                                                tax_or_base='base', move_type='regular')
                    balance_refund = self.compute_balance(wizard, aml_purchase_line, pur_tax.id,
                                                          tax_or_base='tax', move_type='refund')
                    balance_refund_adjustment = self.compute_adjustment(wizard, aml_purchase_line, pur_tax.id,
                                                                        tax_or_base='tax', move_type='refund')
                    base_balance_refund = self.compute_balance(wizard, aml_purchase_line, pur_tax.id,
                                                               tax_or_base='base', move_type='refund')                    
                    base_balance = (base_balance_regular + base_balance_refund)
                    balance = balance_regular + balance_refund + balance_refund_adjustment
                    res[pur_tax.tax_group_id] = res.get(pur_tax.tax_group_id, {})
                    res[pur_tax.tax_group_id][pur_tax] = res[pur_tax.tax_group_id].get(pur_tax, {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0})
                    res[pur_tax.tax_group_id][pur_tax]['balance'] += balance
                    res[pur_tax.tax_group_id][pur_tax]['base_balance'] += base_balance
                    res[pur_tax.tax_group_id][pur_tax]['adjustment'] += balance_refund_adjustment
        return res

    def generate_xlsx_report(self, workbook, data, wizard):
        company_id = wizard.company_id.id
        company = self.env['res.company'].browse(company_id)
        to_date = wizard.to_date
        to_date1 = str(to_date)
        tax_year = to_date1[0:4]
        from_date = wizard.from_date
        vat_return_period = "From: " + from_date + " To: " + to_date

        format1 = workbook.add_format({'font_size': 11, 'bg_color': '#E0FFFF', 'bold':True, 'font_name': 'Arial', 'border':True, 'align': 'center'})
        format2 = workbook.add_format({'font_size': 10, 'bg_color': '#E0FFFF', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'border': True, 'align': 'center'})
        format4 = workbook.add_format({'font_size': 10, 'bg_color': '#E0FFFF', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'left'})
        format5 = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'border': True, 'align': 'right'})
        format6 = workbook.add_format({'font_size': 10, 'bg_color': '#E0FFFF', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'right'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#A9A9A9', 'bold': True, 'font_name': 'Arial', 'border': True, 'align': 'right'})
        format8 = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'border': True, 'align': 'left'})

        sheet = workbook.add_worksheet("VAT Return Report")
        sheet.set_column('A:A', 35)
        sheet.set_column('B:I', 15)
        sheet.merge_range('A3:G3', "VAT Return Report", format1)
        sheet.merge_range('A6:B6', 'Taxable Person Details', format2)

        sheet.write(6, 0, 'TRN', format2)
        sheet.write(6,1,company.vat, format3)

        sheet.write(7, 0, 'Taxable Person Name', format2)
        sheet.write(7, 1, company.name, format3)

        sheet.merge_range('A9:B9', 'Tax Year', format2)
        sheet.merge_range('A11:B11', tax_year, format3)

        sheet.merge_range('C9:D9', 'VAT Return Period', format2)
        sheet.merge_range('C11:D11', vat_return_period, format3)

        sheet.merge_range('A13:B13', 'VAT on Sales and all other outputs', format4)

        sheet.write(13, 0, 'Standard rated supplies', format4)
        sheet.write(13, 1, 'Amount(AED)', format6)
        sheet.write(13, 2, 'VAT Amount(AED)', format6)
        sheet.write(13, 3, 'Adjustment(AED)', format6)

        row = 14
        country = self.env['res.country'].search([('code', '=', 'AE')])
        uae_state = self.env['res.country.state'].search([('country_id','=',country.id)])
        res_partner_obj = self.env['res.partner']
        sale_amount_total = 0.0
        sale_vat_total = 0.0
        sale_adj_total = 0.0
        zero_amount_total = 0.0
        exempt_amount_total = 0.0
        out_scope_amount_total = 0.0
        sale_result = self.get_sale_data(wizard)   
        sale_tax_accounts = self.get_tax_accounts(wizard.company_id.id, type_tax_use='sale')
        purchase_tax_accounts = self.get_tax_accounts(wizard.company_id.id, type_tax_use='purchase')
        tax_groups = self.get_tax_groups()        
        for state in uae_state:
            sheet.write(row, 0, 'Standard rated supplies ' + state.name, format8)
            res = {'regular': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
            for tax_group in tax_groups.filtered(lambda r: r.type == 'regular'):
                sale_data = sale_result.get(tax_group, {})
                sale_data = sale_data.get(state.country_id, {})
                sale_data = sale_data.get(state, {})
                balance = 0.0
                base_balance = 0.0
                adjustment = 0.0
                for sale_tax, sl_data in sale_data.items():
                    balance += sl_data['balance']
                    base_balance += sl_data['base_balance']
                    adjustment += sl_data['adjustment']                
                if tax_group.type == 'regular':
                    res['regular']['balance'] += balance
                    res['regular']['base_balance'] += base_balance
                    res['regular']['adjustment'] += adjustment
            for type, sl_data in res.items():
                if type == 'regular':         
                    sheet.write(row, 1, sl_data['base_balance'], format5)
                    sale_amount_total += sl_data['base_balance']
                    sheet.write(row, 2, sl_data['balance'], format5)
                    sale_vat_total += sl_data['balance']
                    sheet.write(row, 3, sl_data['adjustment'], format5)
                    sale_adj_total += sl_data['adjustment']                    
            row += 1
            
        sheet.write(row,0,'Supplies subject to the reverse charge provisions', format8)        
        res = {'reverse': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
        for tax_group in tax_groups.filtered(lambda r: r.type == 'reverse'):
            tax_data = sale_result.get(tax_group, {})
            balance = 0.0
            base_balance = 0.0
            adjustment = 0.0
            for country, state_data in tax_data.items():
                for state, sale_data in state_data.items():
                    for sale_tax, sl_data in sale_data.items():
                        balance += sl_data['balance']
                        base_balance += sl_data['base_balance']
                        adjustment += sl_data['adjustment']    
            if tax_group.type == 'reverse':
                res['reverse']['balance'] += balance
                res['reverse']['base_balance'] += base_balance
                res['reverse']['adjustment'] += adjustment
        for type, sl_data in res.items():
            if type == 'reverse':         
                sheet.write(row, 1, sl_data['base_balance'], format5)
                sale_amount_total += sl_data['base_balance']
                sheet.write(row, 2, sl_data['balance'], format5)
                sale_vat_total += sl_data['balance']
                sheet.write(row, 3, sl_data['adjustment'], format5)
                sale_adj_total += sl_data['adjustment']                
        row += 1        
        
        sheet.write(row,0,'Zero rated supplies', format8)        
        res = {'zero': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
        for tax_group in tax_groups.filtered(lambda r: r.type == 'zero'):
            tax_data = sale_result.get(tax_group, {})
            balance = 0.0
            base_balance = 0.0
            adjustment = 0.0
            for country, state_data in tax_data.items():
                for state, sale_data in state_data.items():
                    for sale_tax, sl_data in sale_data.items():
                        balance += sl_data['balance']
                        base_balance += sl_data['base_balance']
                        adjustment += sl_data['adjustment']    
            if tax_group.type == 'zero':
                res['zero']['balance'] += balance
                res['zero']['base_balance'] += base_balance
                res['zero']['adjustment'] += adjustment
        for type, sl_data in res.items():
            if type == 'zero':         
                sheet.write(row, 1, sl_data['base_balance'], format5)
                sale_amount_total += sl_data['base_balance']
                sheet.write(row, 2, sl_data['balance'], format5)
                sale_vat_total += sl_data['balance']
                sheet.write(row, 3, sl_data['adjustment'], format5)
                sale_adj_total += sl_data['adjustment']
                
        row += 1 
              
        other_amount_total = 0.0        
        sheet.write(row,0,'Supplies of good and services to registered customers in other GCC implementing states', format8)
        sheet.write(row, 1, other_amount_total, format5)
        sale_amount_total += other_amount_total
        sheet.write(row, 2, 'N/A', format5)
        sheet.write(row, 3, 'N/A', format5)
        row += 1

        sheet.write(row, 0, 'Exempt supplies', format8)                
        res = {'exempt': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
        for tax_group in tax_groups.filtered(lambda r: r.type == 'exempt'):
            tax_data = sale_result.get(tax_group, {})
            balance = 0.0
            base_balance = 0.0
            adjustment = 0.0
            for country, state_data in tax_data.items():
                for state, sale_data in state_data.items():
                    for sale_tax, sl_data in sale_data.items():
                        balance += sl_data['balance']
                        base_balance += sl_data['base_balance']
                        adjustment += sl_data['adjustment']    
            if tax_group.type == 'exempt':
                res['exempt']['balance'] += balance
                res['exempt']['base_balance'] += base_balance
                res['exempt']['adjustment'] += adjustment
        for type, sl_data in res.items():
            if type == 'exempt':         
                sheet.write(row, 1, sl_data['base_balance'], format5)
                sale_amount_total += sl_data['base_balance']
                sheet.write(row, 2, sl_data['balance'], format5)
                sale_vat_total += sl_data['balance']
                sheet.write(row, 3, sl_data['adjustment'], format5)
                sale_adj_total += sl_data['adjustment']
                
        row += 1

        sheet.write(row, 0, 'Out of scope supplies', format8)                
        res = {'out_scope': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
        for tax_group in tax_groups.filtered(lambda r: r.type == 'out_scope'):
            tax_data = sale_result.get(tax_group, {})
            balance = 0.0
            base_balance = 0.0
            adjustment = 0.0
            for country, state_data in tax_data.items():
                for state, sale_data in state_data.items():
                    for sale_tax, sl_data in sale_data.items():
                        balance += sl_data['balance']
                        base_balance += sl_data['base_balance']
                        adjustment += sl_data['adjustment']    
            if tax_group.type == 'out_scope':
                res['out_scope']['balance'] += balance
                res['out_scope']['base_balance'] += base_balance
                res['out_scope']['adjustment'] += adjustment
        for type, sl_data in res.items():
            if type == 'out_scope':         
                sheet.write(row, 1, sl_data['base_balance'], format5)
                sale_amount_total += sl_data['base_balance']
                sheet.write(row, 2, sl_data['balance'], format5)
                sale_vat_total += sl_data['balance']
                sheet.write(row, 3, sl_data['adjustment'], format5)
                sale_adj_total += sl_data['adjustment']
                
        row += 1

        customs_amount_total = 0.0 
        customs_vat_total = 0.0     
        sheet.write(row, 0, 'Import VAT accounted through UAE customs', format8)
        sheet.write(row, 1, customs_amount_total, format5)
        sale_amount_total += customs_amount_total
        sheet.write(row, 2, customs_vat_total, format5)
        sale_vat_total += customs_vat_total
        sheet.write(row, 3, 'N/A', format5)
        row += 1

        corrections_amount_total = 0.0  
        corrections_vat_total = 0.0          
        sheet.write(row, 0, 'Amendments or corrections to Output figures', format8)
        sheet.write(row, 1, corrections_amount_total, format5)
        sale_amount_total += corrections_amount_total
        sheet.write(row, 2, corrections_vat_total, format5)
        sale_vat_total += corrections_vat_total
        sheet.write(row, 3, 'N/A', format5)
        row += 1                    
                        
        sheet.write(row, 0, 'Totals', format4)
        sheet.write(row, 1, sale_amount_total, format7)
        sheet.write(row, 2, sale_vat_total, format7)
        sheet.write(row, 3, sale_adj_total, format7)
        row += 2

        sheet.write(row, 0, 'VAT on Expenses and all other outputs', format4)
        row +=1

        sheet.write(row, 0, 'Standard rated expenses', format4)
        sheet.write(row, 1, 'Amount(AED)', format6)
        sheet.write(row, 2, 'VAT Amount(AED)', format6)
        sheet.write(row, 3, 'Adjustment(AED)', format6)
        row += 1        

        purchase_amount_total = 0
        purchase_vat_total = 0
        purchase_adj_total = 0
        purchase_result = self.get_purchase_data(wizard)     
        sheet.write(row,0,'Standard rated expenses', format8)       
        res = {'expense': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
        for tax_group in tax_groups.filtered(lambda r: r.type != 'reverse'):
            tax_data = purchase_result.get(tax_group, {})
            balance = 0.0
            base_balance = 0.0
            adjustment = 0.0
            for pur_tax, pur_data in tax_data.items():
                balance += pur_data['balance']
                base_balance += pur_data['base_balance']
                adjustment += pur_data['adjustment']    
            if tax_group.type != 'reverse':
                res['expense']['balance'] += balance
                res['expense']['base_balance'] += base_balance
                res['expense']['adjustment'] += adjustment
        for type, pur_data in res.items():
            if type == 'expense':         
                sheet.write(row, 1, pur_data['base_balance'], format5)
                purchase_amount_total += pur_data['base_balance']
                sheet.write(row, 2, pur_data['balance'], format5)
                purchase_vat_total += pur_data['balance']
                sheet.write(row, 3, pur_data['adjustment'], format5)
                purchase_adj_total += pur_data['adjustment']                
        row += 1 
            
        sheet.write(row,0,'Supplies subject to the reverse charge provisions', format8)       
        res = {'reverse': {'balance': 0.0, 'base_balance': 0.0, 'adjustment': 0.0}}
        for tax_group in tax_groups.filtered(lambda r: r.type == 'reverse'):
            tax_data = purchase_result.get(tax_group, {})
            balance = 0.0
            base_balance = 0.0
            adjustment = 0.0
            for pur_tax, pur_data in tax_data.items():
                balance += pur_data['balance']
                base_balance += pur_data['base_balance']
                adjustment += pur_data['adjustment']    
            if tax_group.type == 'reverse':
                res['reverse']['balance'] += balance
                res['reverse']['base_balance'] += base_balance
                res['reverse']['adjustment'] += adjustment
        for type, pur_data in res.items():
            if type == 'reverse':         
                sheet.write(row, 1, pur_data['base_balance'], format5)
                purchase_amount_total += pur_data['base_balance']
                sheet.write(row, 2, pur_data['balance'], format5)
                purchase_vat_total += pur_data['balance']
                sheet.write(row, 3, pur_data['adjustment'], format5)
                purchase_adj_total += pur_data['adjustment']                
        row += 1

        corrections_amount_total = 0.0  
        corrections_vat_total = 0.0          
        sheet.write(row, 0, 'Amendments or corrections to Input figures', format8)
        sheet.write(row, 1, corrections_amount_total, format5)
        purchase_amount_total += corrections_amount_total
        sheet.write(row, 2, corrections_vat_total, format5)
        purchase_vat_total += corrections_vat_total
        sheet.write(row, 3, 'N/A', format5)
        row += 1
        
        
        sheet.write(row, 0, 'Totals', format4)
        sheet.write(row, 1, purchase_amount_total, format7)
        sheet.write(row, 2, purchase_vat_total, format7)
        sheet.write(row, 3, purchase_adj_total, format7)
        row += 2

        sheet.write(row, 0, 'Net VAT due', format4)
        row += 1

        sheet.write(row, 0, 'Total value of due tax for the period', format4)
        due_tax = sale_vat_total+sale_adj_total
        sheet.write(row, 1, due_tax, format7)
        row += 1

        sheet.write(row, 0, 'Total value of recoverable tax for the period', format4)
        recover_tax = purchase_vat_total - purchase_adj_total
        sheet.write(row, 1, recover_tax, format7)
        row += 1

        sheet.write(row, 0, 'Net VAT due(or reclaimed) for the period', format4)
        due_vat = due_tax + recover_tax
        sheet.write(row, 1, due_vat, format7)
        row += 1
