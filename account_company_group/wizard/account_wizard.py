# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountAccountTemplate(models.TransientModel):
      _name ='account.template.wizard'
      _description ='Account Template'


      company_id = fields.Many2one('res.company',string='Company',domain=[('parent_id', '=', None)])
      company_ids = fields.Many2many('res.company',string='Child Companies')
      chart_template_id = fields.Many2one('account.chart.template', string='Template')
      
    
      @api.onchange('company_id')
      def _onchange_company_id(self):
        self.company_ids = []
        if self.company_id:
            return {'domain': {'company_ids': [('parent_id', '=', self.company_id.id)]}}
    
      


      @api.multi
      def account_chart(self):
          self.chart_template_id.with_context(company_ids=self.company_ids,multiple_company=True).load_for_current_company(15.0, 15.0)
          
           
      









