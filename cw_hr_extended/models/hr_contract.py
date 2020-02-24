# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class HrContract(models.Model):
    _inherit = "hr.contract"
    
    @api.multi
    @api.depends('employee_id')
    def _compute_employee_data(self):
        for contract in self:
            permit_no = False
            visa_no = False
            visa_expire = False
            visa_type_id = self.env['hr.visa.type']
            employee_id = contract.sudo(SUPERUSER_ID).employee_id
            if employee_id:
                permit_no = employee_id.permit_no
                visa_no = employee_id.visa_no
                visa_expire = employee_id.visa_expire
                visa_type_id = employee_id.visa_type_id                
            contract.update({'permit_no': permit_no,
                             'visa_no': visa_no,
                             'visa_expire': visa_expire,
                             'visa_type_id': visa_type_id})    

    #trial_date_start = fields.Date('Start of Trial Period')
    permit_no = fields.Char(compute="_compute_employee_data", store=True, readonly=True, copy=False)
    visa_no = fields.Char(compute="_compute_employee_data", store=True, readonly=True, copy=False)
    visa_expire = fields.Date(compute="_compute_employee_data", store=True, readonly=True, copy=False)
    visa_type_id = fields.Many2one('hr.visa.type', string='Visa Type', compute="_compute_employee_data", store=True, readonly=True, copy=False)
    
    '''@api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.permit_no = self.employee_id.permit_no
            self.visa_no = self.employee_id.visa_no
            self.visa_expire = self.employee_id.visa_expire
            self.visa_type_id = self.employee_id.visa_type_id
        res = super(HrContract, self)._onchange_employee_id()
        return res'''