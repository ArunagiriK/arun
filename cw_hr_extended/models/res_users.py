# -*- coding: utf-8 -*-

import pytz
import datetime
import logging

from collections import defaultdict
from itertools import chain, repeat
from lxml import etree
from lxml.builder import E

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.service.db import check_super
from odoo.tools import partition

_logger = logging.getLogger(__name__)
    

class Users(models.Model):    
    _inherit = "res.users"
    
    @api.multi
    @api.constrains('employee_ids')
    def _check_no_employees(self):       
        for user in self:
            nemployees = sum(user.mapped('employee_ids'))
            if nemployees > 1:
                raise ValidationError(_('A user can be associated to one employee only!'))
    
    
    @api.multi
    @api.constrains('employee_ids', 'company_id')
    def _check_empcompany_usercompany(self):       
        for user in self:
            for employee in user.employee_ids:
                if user.company_id != employee.company_id:
                    raise ValidationError(_('The company of related user and company of employee should be same!'))
    

class Partner(models.Model):
    
    _inherit = "res.partner"    
    
    tz = fields.Selection(default=lambda self: self._context.get('tz', 'Asia/Dubai'))
    
    
