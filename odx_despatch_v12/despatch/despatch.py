# -*- coding: utf-8 -*-
from odoo import models,api,fields
from odoo.exceptions import Warning,RedirectWarning


class Despatch(models.Model):
    _name ='od.despatch'

    @api.depends('od_dispatch_line.amount')
    def _compute_od_amount(self):
        amount = 0
        od_dispatch_line = self.od_dispatch_line
        for line in od_dispatch_line:
            amount = amount + line.amount
        self.od_amount = amount
        
    

    def default_od_journal_id(self):
        journal_id = False
        journal = self.env['account.journal']
        journal_ob = journal.search([('name','=','JOURNAL VOUCHER')])
        if journal_ob:
            journal_id = journal_ob.id
        return journal_id
    
    
    name = fields.Char(string="Name",required=True)
    partner_id = fields.Many2one('res.partner',string='Customer')
    invoice_ids = fields.Many2many('account.invoice', 'desp_id', 'invoice_id', string='Invoices')
    
    od_transport_type = fields.Selection([('own','Own Transportation'),('third','Third Party')],string="Transportation Type",default='own')
    od_carton_no = fields.Char(string="No.Of Cartons")
    no_of_carton = fields.Integer(string="Cartons Count")
    od_packaging_no = fields.Char(string="Packaging")
    od_despatch_state = fields.Selection([
            ('ready_to_dispatch','Ready To Despatch'),
            ('despatched','Despatched'),
        ],string="Despatch State",default='ready_to_dispatch')
    od_despatch_date = fields.Date(string="Despatch Date")
    od_narration = fields.Char(string="Narration")
    od_transporter_id = fields.Many2one('res.partner', string='Transporter')
    od_driver_id = fields.Many2one('res.users', string='Driver')
    od_desc = fields.Text(string='Note')
    od_state_id = fields.Many2one('res.country.state', string='Destination')
    od_deliveryloc_id = fields.Many2one('od.delivery.loc',string='Delivery Location')
    od_trans_ref = fields.Char(string="Transporter Ref")
    od_transporter_inv_ref = fields.Char(string='Transporter Inv Ref')
    od_transporter_inv_date = fields.Date(string='Transporter Inv Date')
    od_amount = fields.Float(compute='_compute_od_amount', string='Amount', readonly=True, store=True)
    od_transit_days = fields.Integer(string='Transit Days')
    od_delivery_date = fields.Date(string='Delivery Date')
    od_stamp = fields.Boolean(string='Receipt Copy Collection')
    od_stamp_date = fields.Date(string='Receipt Date')
    od_attachement = fields.Binary(string="Attachement")
    od_filename = fields.Char(string="Filename")
    od_dispatch_line = fields.One2many('od.dispatch.info.line','desp_id',string='Dispatch Line')    
    od_help_lines = fields.One2many('od.helper.line','desp_id',string="Helpers")
    od_delivery_assis_ids = fields.Many2many('res.users','rel_desp_despath_user','desp_id','user_id',string="Delivery Assistance")
    od_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle Reg No")
    od_trans_acc_id = fields.Many2one('account.account',string="Transportation Charge")
    od_move_id = fields.Many2one('account.move',string="Entry",readonly=True,copy=False)
    od_journal_id = fields.Many2one('account.journal',string="Journal",default=default_od_journal_id)
    od_desp_confirm = fields.Boolean(string='Confirmed',copy=False)
    date_invoice = fields.Date(string='Invoice Date')
    number = fields.Char('Number')
    user_id = fields.Many2one('res.users',string='Salesperson')
    
    
    @api.constrains('od_dispatch_line','no_of_carton')
    def check_carton_count(self):
        line_count = sum([line.no_ofcarton for line in self.od_dispatch_line])
        no_of_carton = self.no_of_carton
        if line_count > no_of_carton:
            raise Warning("Check the Carton Count With Line")
    
    @api.onchange('od_state_id')
    def onchange_od_state_id(self):
        if self.od_state_id:
            self.od_transit_days = self.od_state_id.od_transit_days  
            
            
    @api.one
    def od_confirm(self):
        if self.od_transport_type == 'third':            
            self.od_create_move()
        self.write({'od_despatch_state':'despatched'})
        for invoice_id in self.invoice_ids:
            invoice_id.od_despatch_state = 'despatched'
#             self.od_send_mail('email_despath_bfly_edi_invoice')
    
   
    @api.one
    def od_send_mail(self,template):
        ir_model_data = self.env['ir.model.data']
        mail_obj = self.env['mail.template']
        template_id = ir_model_data.get_object_reference('odx_despatch_v12', template)[1]
        template = mail_obj.browse(template_id)
        user = self.env.user
        template.with_context(lang=user.lang).send_mail(self.id, force_send=True, raise_exception=False)
        return True
    
    def od_create_move(self):
        
        move_obj = self.env['account.move']
        date = self.od_despatch_date
        ref = self.od_narration
        if not ref:
            raise Warning("Narration Should Be Filled") 
        
        trans =self.od_transporter_id
        if not trans:
            raise Warning("Transporter Should Be Filled")
        partner_id = self.partner_id and self.partner_id.id
        amount = self.od_amount
        journal_id = self.od_journal_id and self.od_journal_id.id
        if not journal_id:
            raise Warning("Journal Should Be Filled")
        debit_account = self.od_trans_acc_id.id
        if not debit_account:
            raise Warning("Transportation Account Should Be Filled")
        credit_account = self.od_transporter_id and self.od_transporter_id.property_account_payable_id and self.od_transporter_id.property_account_payable_id.id or False
      
        move_lines =[]

        vals1={
                'name': ref,
                'ref': ref,
                'journal_id': journal_id,
                'date': date,
                'account_id': credit_account,
                'debit': 0.0,
                'credit': abs(amount),
                'partner_id': self.od_transporter_id and self.od_transporter_id.id or False,
               

            }
        vals2={
                'name': ref,
                'ref': ref,
               
                'journal_id': journal_id,
                'date': date,
                'account_id': debit_account,
                'credit': 0.0,
                'debit': abs(amount),
                'partner_id': partner_id,
               

            }
        move_lines.append([0,0,vals1])
        move_lines.append([0,0,vals2])
          
        move_vals = {

                'date': date,
                'ref': ref,
                'journal_id': journal_id,
                'line_ids':move_lines

                }
        move = move_obj.create(move_vals)
        move.post()
        move_id = move.id
        self.od_move_id = move_id
        self.od_desp_confirm = True
        
        return True
    
class  ODDispatchInfoLine(models.Model):
    _name = "od.dispatch.info.line"
    @api.one
    @api.depends('no_ofcarton', 'unit_price')
    def _compute_amount(self):
        self.amount = self.no_ofcarton * self.unit_price
       
    
    
    @api.onchange('cartonsize_id', 'od_transporter_id','od_state_id')
    def _onchange_cartonsize_id(self):
        price = 0
        if self.cartonsize_id and self.od_transporter_id and self.od_state_id:
            tran_pricelist = self.env['od.transporter.pricelist'].search([('transporter_id','=',self.od_transporter_id.id),('state_id','=',self.od_state_id.id),('od_cartonsize_id','=',self.cartonsize_id.id)],limit=1)
            price = tran_pricelist.unit_price
            self.unit_price = price

    cartonsize_id = fields.Many2one('od.cartonsize',string='Carton Size')
    desp_id = fields.Many2one('od.despatch',string="Despatch")
    inv_id = fields.Many2one('account.invoice',string='Invoice')
    unit_price = fields.Float('Unit Rate')
    no_ofcarton = fields.Float(string="No.of Carton")
    amount = fields.Float(compute='_compute_amount', string='Amount', readonly=True, store=True)
    od_transporter_id = fields.Many2one(related='inv_id.od_transporter_id', store=True, string='Transporter')
    od_state_id = fields.Many2one(related='inv_id.od_state_id', store=True, string='State')

class ODHelperLines(models.Model):
    _name = 'od.helper.line'
    desp_id = fields.Many2one('od.despatch',string="Despatch")
    invoice_id = fields.Many2one('account.invoice',string="Invoice")
    user_id = fields.Many2one('res.users',string="Helpers")

    
    
    