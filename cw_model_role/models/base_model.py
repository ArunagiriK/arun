# -*- coding: utf-8 -*-

from odoo.models import BaseModel

#setattr(BaseModel, _employee_id, False)
#setattr(BaseModel, _user_id, False)

BaseModel._employee_id = False
BaseModel._user_id = False