# -*- coding: utf-8 -*-
from odoo import models,api,fields
from odoo.exceptions import Warning,RedirectWarning
import re
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta 


class DespatchInvoiceList(models.Model):
    _name ='od.despatch.invoice.list'
    _order = "partner_id,inv_date"
    
    partner_id = fields.Many2one('res.partner',string='Customer')
    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    requested_date = fields.Date(string="Requested Date")
    amount = fields.Float(string="Amount")
    inv_date = fields.Date(string="Invoice Date")
    so_no = fields.Char('So Number')
    client_order_ref = fields.Char(string='Customer Reference')
    state_id = fields.Many2one('res.country.state',string="State")
    user_id = fields.Many2one('res.users',string="Salesperson")
    
    
    @api.multi
    def open_despatch_wizard(self):
        despatch_obj = self.env['od.despatch.invoice.list'].browse(self._context.get('active_ids'))
            
        despatch_ids = []
        custom_ids = []
        so_ids = []

        for des in despatch_obj:
            custom_ids.append(des.partner_id and des.partner_id.id)
            vals = (0,0,{'invoice_id':des.invoice_id and des.invoice_id.id,
                    'partner_id':des.partner_id and des.partner_id.id})
            despatch_ids.append(vals)
            
        custom_ids = list(set(custom_ids))  
        for cust in custom_ids:
            sale_obj = self.env['sale.order'].search([('partner_id','=',cust),('od_dms','not in',('invoiced','cancel'))])
            for sale in sale_obj:
                val = (0,0,{'partner_id':sale.partner_id and sale.partner_id.id,
                    'so_id':sale and sale.id,
                    'client_order_ref':sale.client_order_ref,
                    'date':sale.date_order,
                    'requested_date':sale.requested_date,
                    'amount':sale.amount_total,
                    'state_id':sale.partner_id and sale.partner_id.state_id and sale.partner_id.state_id.id or False})
                    
                    
                so_ids.append(val)

        

        name = self.env['ir.sequence'].next_by_code('od.despatch.checklist')
        
        wizard_obj = self.env['od.despatch.new.wizard'].create({'name':name,'wizard_line':despatch_ids,'so_wizard_line':so_ids,'document_date':str(datetime.now())})            
        return {
            'name':'Despatch',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'od.despatch.new.wizard',
            'res_id': wizard_obj.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def load_despatch_line(self):
        current_despach_ids = []
        all_inv_ids = []
        current_despatch_lines = self.search([])
        for des in current_despatch_lines:
            all_inv_ids.append(des and des.invoice_id and des.invoice_id.id)
            if des.invoice_id.od_despatch_state != 'ready_to_dispatch':
                current_despach_ids.append(des.id)
                
        
        self.browse(current_despach_ids).unlink()
        invoice_obj = self.env['account.invoice'].search([('state','not in',('draft','cancel')),('type','=','out_invoice')])
        for inv in invoice_obj:
            # print 'AAAAAAAAAAA',inv.journal_id
            # print inv
            if inv.od_despatch_state == 'ready_to_dispatch' and inv.id not in all_inv_ids and inv.journal_id.id != 8:
                data_obj = {}
                data_obj['invoice_id'] = inv and inv.id
                data_obj['partner_id'] = inv and inv.partner_id and inv.partner_id.id
                data_obj['requested_date'] = inv and inv.od_requested_date
                data_obj['amount'] = inv and inv.amount_total
                
                
                data_obj['inv_date'] = inv and inv.date_invoice
                data_obj['so_no'] = inv and inv.origin
                sale_obj = self.env['sale.order'].search([('name','=',inv.origin)])
                client_order_ref = sale_obj and sale_obj.client_order_ref or ''
                data_obj['client_order_ref'] = client_order_ref
                data_obj['state_id'] = inv and inv.partner_id and inv.partner_id.state_id and inv.partner_id.state_id.id
                
                data_obj['user_id'] = inv and inv.user_id and inv.user_id.id
                self.create(data_obj)
                
        action = self.env.ref('odx_despatch_v12.action_despatch_invice_list_view')
        result = action.read()[0] 
        return result            

       
            


    
