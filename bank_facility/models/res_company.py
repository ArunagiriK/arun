# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class res_company(models.Model):
    _inherit = 'res.company'

    facility_total= fields.Float('Total Facility',compute='_company_count')
    facility_total_child = fields.Float('Total Facility')
    facility_available = fields.Float('Facility Available',compute='_company_count')
    facility_available_child = fields.Float('Facility Available',compute ='_company_count')
    facility_utilized = fields.Float('Facility utilized',compute='_company_count')
    facility_utilized_child = fields.Float('Facility utilize')
    faciltity_utilized_given = fields.Float('Facility utilized')
    
    @api.multi 
    @api.constrains('facility_total_child','faciltity_utilized_given')
    def collection_date_validation(self):
        companies = self.search([('parent_id','!=',None)])
        for r in companies:
            if r.facility_total_child:
                if r.faciltity_utilized_given > r.facility_total_child:
                        raise ValidationError("Facility utilize should not be greater than Total utilize.!")


    @api.multi
    @api.depends('facility_total_child','facility_available_child','faciltity_utilized_given')
    def _company_count(self):
        total_facility = self.env['res.company'].search([('id','=',1)])
        total_facility_val = 0.0
        total_utilized_val = 0.0
        total_vailable = 0.0
        no_of_companies = self.search([('parent_id','!=',None)])
        for c in no_of_companies:
            total_utilized_val += c.faciltity_utilized_given
            total_vailable += c.facility_available_child
            c.facility_available_child =   c.facility_total_child - c.faciltity_utilized_given
            total_facility_val += c.facility_total_child
        total_facility.facility_utilized = total_utilized_val
        total_facility.facility_available = total_vailable
        total_facility.facility_total = total_facility_val
        
    
    

    
