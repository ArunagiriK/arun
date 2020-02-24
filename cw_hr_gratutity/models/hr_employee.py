# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = "hr.employee"