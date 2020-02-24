# -*- coding: utf-8 -*-
import logging
import psycopg2
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
import base64

_logger = logging.getLogger(__name__)


class BankFacility(models.Model):
      _name = 'bank.facility'
      _description = 'Bank Facility'


      name = fields.Char('Name')
      active = fields.Boolean('Active' ,default=True)
      amount = fields.Float('Amount')
      payment_date = fields.Date('Date')
      partner_id = fields.Many2one('res.partner', string='Partner')
      interest_percentage = fields.Float('Interest Percentage')
      company_id = fields.Many2one('res.company',related='journal_id.company_id',string='Company')
      journal_id = fields.Many2one('account.journal','Journal')
      new_account_type = fields.Selection([('bank_faciltiy','Bank Facility'),('balansheet','Balansheet'),('liability','Liability')],string='New account type')
      charges_details = fields.Char('Charges Details')
      currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
      facility_interest_charges = fields.Many2one('account.account','Facility Interest Charges A/c ')
      facility_account_payable = fields.Many2one('account.account','Facility Payable Account A/c')
      faciltiy_type = fields.Selection([('od','OD'),('discount','Discount'),('bill_payment','Bill Payment Lc')],string='Facility Type',default='od')
      interest_details = fields.Many2one('account.account','Expense and Payable A/c')
      payment_type =fields.Selection([('payment_auto','Auto Payment'),('manual','Manual')],string='Payment')
      #~ move_id = fields.Many2one('account.move', string='Journal Entry',
        #~ readonly=True, index=True, ondelete='restrict', copy=False,
        #~ help="Link to the automatically generated Journal Items.")
      state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'),('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
  
          
      @api.multi
      def action_draft(self):
        return self.write({'state': 'draft'})
      
      
             







