# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class DespatchReport(models.Model):
    _name = "despatch.report"
    _description = "Despatch Report"
    _auto = False
    _rec_name = 'partner_id'
    _order = 'partner_id'

    type = fields.Selection([('own','Own Transportation'),('third','Third Party')],string="Transportation Type",default='own')
    od_transporter_inv_ref = fields.Char(string='Transporter Inv Ref')
    ref = fields.Char(string='Ref')
    od_transporter_inv_date = fields.Date(string='Transporter Inv Date')
    amount = fields.Float( string='Amount', readonly=True, store=True)
    partner_id = fields.Many2one('res.partner', 'Partner',)
    invoice = fields.Char('Invoice')
    user_id = fields.Many2one('res.users', 'Salesperson')
    journal_id = fields.Many2one('account.journal', 'Sales Type',)
    od_journal_id = fields.Many2one('account.journal',string="Journal")
    od_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle Reg No")
    od_trans_acc_id = fields.Many2one('account.account',string="Transportation Charge")
    depatch_description = fields.Char('Dispatch Desc')
    od_carton_no = fields.Char(string="Carton")
    od_transporter_id = fields.Many2one('res.partner', string='Transporter')
    od_state_id = fields.Many2one('res.country.state', string='Destination')
    od_driver_id = fields.Many2one('res.users', string='Driver')
    od_despatch_date = fields.Date(string="Despatch Date")
    od_despatch_state = fields.Selection([
            ('ready_to_dispatch','Ready To Despatch'),
            ('despatched','Despatched'),
        ],string="Despatch State",default='ready_to_dispatch')
    
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'despatch_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW despatch_report AS (
 
             SELECT ROW_NUMBER () OVER (ORDER BY a.id ) AS id,
a.partner_id as partner_id,
a.number as invoice,
a.name as ref,
a.user_id as user_id,
a.journal_id as journal_id,
a.od_desc as depatch_description,
a.od_carton_no as od_carton_no,
    a.od_transport_type as type,
 a.od_transporter_inv_ref,
 a.od_transporter_inv_date,
 a.od_journal_id,
 a.od_trans_acc_id,
 a.od_fleet_id,
 a.od_amount as amount,
a.od_transporter_id as od_transporter_id,
a.od_state_id as od_state_id,
a.od_driver_id as od_driver_id,
a.od_despatch_date as od_despatch_date,
a.od_despatch_state as od_despatch_state
                FROM account_invoice AS a
WHERE a.type = 'out_invoice'
            GROUP BY a.id,
a.partner_id,
a.number,
a.user_id,
a.journal_id,
a.od_desc,
a.od_carton_no,
a.od_transporter_id,
a.od_state_id,
a.od_driver_id,
a.od_despatch_date,
a.od_despatch_state
                
                    
            )
        """)
