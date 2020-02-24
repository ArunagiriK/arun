# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.exceptions import Warning, RedirectWarning
import odoo.addons.decimal_precision as dp


class Invoice(models.Model):
    _inherit = "account.invoice"
     
    @api.one
    @api.depends('od_dispatch_line.amount')
    def _compute_od_amount(self):
        amount = 0
        od_dispatch_line = self.od_dispatch_line
        for line in od_dispatch_line:
            amount = amount + line.amount
        self.od_amount = amount
        

    @api.onchange('origin')
    def onchange_origin(self):
        origin = self.origin
        if origin:
            sale_order = self.env['sale.order'].search([('name','=',origin)])
            requested_date = sale_order.requested_date or False
            self.od_requested_date = requested_date    
    
    def default_od_journal_id(self):
        journal_id = False
        journal = self.env['account.journal']
        journal_ob = journal.search([('name','=','JOURNAL VOUCHER')])
        if journal_ob:
            journal_id = journal_ob.id
        return journal_id
    
    
    desp_ids = fields.Many2many('od.despatch','despatch_inv_rel','invoice_id','despatch_id',string='Despatches', copy=False)
    od_invoice_print = fields.Char(string="Invoice Print Name")
    od_transport_type = fields.Selection([('own','Own Transportation'),('third','Third Party')],string="Transportation Type",default='own')
    od_carton_no = fields.Char(string="No.Of Cartons")
    no_of_carton = fields.Integer(string="Cartons Count")
    od_packaging_no = fields.Char(string="Packaging")
    od_requested_date = fields.Datetime('Requested Date')
    od_despatch_state = fields.Selection([
            ('ready_to_dispatch','Ready To Despatch'),
            ('despatched','Despatched'),
        ],string="Despatch State",default='ready_to_dispatch',copy=False)
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
    od_stamp_date = fields.Date(string='Stamp Received Date')
    od_goods_date = fields.Date(string='Goods Received Date')
    od_stamp_users = fields.Many2one('res.users',string='Stamp Collected By')
    od_attachement = fields.Binary(string="Attachement")
    od_filename = fields.Char(string="Filename")

    od_dispatch_line = fields.One2many('od.dispatch.info.line','inv_id',string='Dispatch Line')
    od_help_lines = fields.One2many('od.helper.line','invoice_id',string="Helpers")
    od_delivery_assis_ids = fields.Many2many('res.users','rel_invoice_despath_user','invoice_id','user_id',string="Delivery Assistant")
    od_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle Reg No")
    od_trans_acc_id = fields.Many2one('account.account',string="Transportation Charge")
    od_move_id = fields.Many2one('account.move',string="Entry",readonly=True,copy=False)
    od_journal_id = fields.Many2one('account.journal',string="Journal",default=default_od_journal_id)
    od_desp_confirm = fields.Boolean(string='Confirmed',copy=False)
    despath_move_id = fields.Many2one('account.move',string="Despatch Entry")

    od_category_id = fields.Many2one('orchid.category',string="Category")
    od_type_id = fields.Many2one('orchid.partner.type', string='Type')
    od_area_id = fields.Many2one('orchid.partner.area', string='Area')
    od_group_id = fields.Many2one('orchid.partner.group',string='Group')
    local_currency = fields.Float(string=' Local Currency',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always', digits=dp.get_precision('Global'))

    od_permit_no = fields.Char('Permit Number')
        

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax

        
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
            self.local_currency = currency_id.compute(self.amount_total, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
        
    @api.constrains('od_dispatch_line','no_of_carton')
    def check_carton_count(self):
        line_count = sum([line.no_ofcarton for line in self.od_dispatch_line])
        no_of_carton = self.no_of_carton
        if line_count > no_of_carton:
            raise Warning("Check the Carton Count With Line")

    @api.multi
    def show_despatch(self):
        action = self.env.ref('odx_despatch_v12.action_od_despatch_tree_view').read()[0]
        invoice_ids = []
        invoice_lines = self.env['od.despatch'].search([('invoice_ids.id','=',self.id)])
        for line in invoice_lines:
            invoice_ids.append(line and line.id)
        domain = []
        domain.append(('id','in',invoice_ids))
        action['domain'] = domain
        return action
    
    @api.onchange('od_state_id')
    def onchange_od_state_id(self):
        if self.od_state_id:
            self.od_transit_days = self.od_state_id.od_transit_days
                
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        company_id = self.company_id.id
        state_id = self.partner_id and self.partner_id.state_id and self.partner_id.state_id.id or False

        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        type = self.type
        if self.partner_id:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('out_invoice', 'out_refund','credit_note'):
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id
            else:
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            addr = self.partner_id.address_get(['delivery'])
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=addr['delivery'])

            bank_id = p.bank_ids and p.bank_ids.ids[0] or False

            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                    }
                if p.invoice_warn == 'block':
                    self.partner_id = False
                return {'warning': warning}
        self.od_invoice_print = self.partner_id and self.partner_id.od_invoice_print or ''
        self.od_state_id = state_id
        self.account_id = account_id
        self.payment_term_id = payment_term_id
        self.fiscal_position_id = fiscal_position

        if type in ('in_invoice', 'in_refund'):
            self.partner_bank_id = bank_id
    
    
    @api.one
    def od_confirm(self):
        if self.od_transport_type == 'third':
            self.write({'od_despatch_state':'despatched'})
            self.od_create_move()
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

class InvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    od_item_code = fields.Char('Item Code')
    od_article_no = fields.Char('Article#')
    od_carton_no = fields.Char(string="Carton")
    od_packaging_no = fields.Char(string="Packaging")
    
    
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
    inv_id = fields.Many2one('account.invoice',string='Invoice')
    unit_price = fields.Float('Unit Rate')
    no_ofcarton = fields.Float(string="No.of Carton")
    amount = fields.Float(compute='_compute_amount', string='Amount', readonly=True, store=True)
    od_transporter_id = fields.Many2one(related='inv_id.od_transporter_id', store=True, string='Transporter')
    od_state_id = fields.Many2one(related='inv_id.od_state_id', store=True, string='State')
#
# class ODHelperLines(models.Model):
#     _name = 'od.helper.line'
#     invoice_id = fields.Many2one('account.invoice',string="Invoice")
#     user_id = fields.Many2one('res.users',string="Helpers")

