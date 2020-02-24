# -*- coding: utf-8 -*-
#
#################################################################################
# Author      : Codeware Computer Trading L.L.C. (<www.codewareuae.com>)
# Copyright(c): 2017-Present Codeware Computer Trading L.L.C.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import logging
import time
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class HrHolidays(models.Model):
    _inherit = 'hr.leave'
    
    active = fields.Boolean(string='Active', default=True)
