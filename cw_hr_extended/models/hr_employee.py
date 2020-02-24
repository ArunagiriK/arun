# -*- coding: utf-8 -*-

import logging
import time
import math
import pytz
from calendar import monthrange
from datetime import date
from datetime import datetime
from datetime import timedelta
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, rrule, MO, TU, WE, TH, FR, SA, SU
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


def float_to_time(float_hour):
    return datetime.time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)


def to_naive_user_tz(datetime, record):
    tz_name = record._context.get('tz') or record.env.user.tz
    tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
    return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(tz).replace(tzinfo=None)


def to_naive_utc(datetime, record):
    tz_name = record._context.get('tz') or record.env.user.tz
    tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
    return tz.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(pytz.UTC).replace(tzinfo=None)


def to_tz(datetime, tz_name):
    tz = pytz.timezone(tz_name)
    return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(tz).replace(tzinfo=None)


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'mail.thread', 'ir.model.role']
    _user_id = 'user_id'
            
    @api.one
    @api.depends('join_date', 'birthday')
    def _compute_dates(self):
        num_of_years = False
        num_of_months = False
        age = False
        current_date = datetime.datetime.now().date()
        if self.sudo(SUPERUSER_ID).join_date:
            join_date = datetime.datetime.strptime(str(self.join_date), '%Y-%m-%d').date()
            diff_bw = relativedelta(current_date, join_date)
            num_of_years = diff_bw.years
            num_of_months = diff_bw.months
        birthday = self.sudo(SUPERUSER_ID).birthday            
        if birthday:
            birthday = datetime.datetime.strptime(str(birthday), '%Y-%m-%d').date()
            age = relativedelta(current_date, birthday).years
        self.num_of_years = num_of_years
        self.num_of_months = num_of_months
        self.age = age
            
    @api.one
    @api.depends('join_date')
    def _compute_anniv_dates(self):
        current_year_anniversary_date = False 
        anniversary_date = False 
        first_anniversary_date = False 
        last_anniversary_date = False 
        last_anniversary_start_date = False 
        last_anniversary_end_date = False
        if self.join_date:
            join_date = datetime.datetime.strptime(str(self.join_date), '%Y-%m-%d').date()
            first_anniversary_date = join_date + relativedelta(years=1)
            current_date = datetime.datetime.now().date()
            #current_date = datetime.now()
            current_year = current_date.year
            #current_month = current_date.month
            current_anniversary_date = join_date.replace(year=current_year)
            current_year_anniversary_date = current_anniversary_date
            anniversary_date = current_anniversary_date
            if current_anniversary_date >= current_date:
                anniversary_date = current_anniversary_date
                #current_anniversary_date = current_anniversary_date - relativedelta(months=-12)
                current_anniversary_date = current_anniversary_date + relativedelta(years=-1)
            else:
                anniversary_date = current_anniversary_date + relativedelta(years=1)
            current_year_anniversary_date = current_year_anniversary_date.strftime(DEFAULT_SERVER_DATE_FORMAT) 
            anniversary_date = anniversary_date.strftime(DEFAULT_SERVER_DATE_FORMAT)                              
            last_anniversary_start_date = current_anniversary_date + relativedelta(years=-1)  
            last_anniversary_end_date = current_anniversary_date - timedelta(days=1) 
            last_anniversary_date = current_anniversary_date.strftime(DEFAULT_SERVER_DATE_FORMAT) 
            last_anniversary_start_date = last_anniversary_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            last_anniversary_end_date = last_anniversary_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.current_year_anniversary_date = current_year_anniversary_date 
        self.first_anniversary_date = first_anniversary_date
        self.anniversary_date = anniversary_date                     
        self.last_anniversary_date = last_anniversary_date           
        self.last_anniversary_start_date = last_anniversary_start_date         
        self.last_anniversary_end_date = last_anniversary_end_date

    @api.multi
    def _search_current_year_anniversary_date(self, operator, value):    
        assert operator in ('=', '!=', '<', '>', '<=', '>='), 'Invalid domain operator'
        assert isinstance(value, (str, unicode, bytes)), 'Invalid value'
        assert isinstance(operator, (str, unicode, bytes)), 'Invalid operator'
        given_date = False
        try:
            given_date = datetime.strptime(value, "%Y-%m-%d")
        except Exception:
            raise ValidationError(_('Please enter the date in "Y-m-d" format.\n You entered %s.')%(value))
        query = """SELECT id FROM 
                    (SELECT *,
                        CASE 
                            WHEN TO_CHAR(CURRENT_DATE, 'YYYY') = TO_CHAR(DATE(join_date + DATE_TRUNC('YEAR', AGE(join_date))), 'YYYY') THEN DATE(join_date + DATE_TRUNC('YEAR', AGE(join_date)))
                            ELSE DATE(join_date + DATE_TRUNC('YEAR', AGE(join_date)) + INTERVAL '1 YEAR')
                        END AS current_year_anniversary_date
                FROM hr_employee) aniv
                WHERE 
                current_year_anniversary_date %s '%s';""" % \
                (str(operator), str(value))
        self.env.cr.execute(query)
        ids = [t[0] for t in self.env.cr.fetchall()]
        return [('id', 'in', ids)]

    @api.multi
    def _search_anniversary_date(self, operator, value):    
        assert operator in ('=', '!=', '<', '>', '<=', '>='), 'Invalid domain operator'
        assert isinstance(value, (str, unicode, bytes)), 'Invalid value'
        assert isinstance(operator, (str, unicode, bytes)), 'Invalid operator'
        given_date = False
        try:
            given_date = datetime.strptime(value, "%Y-%m-%d")
        #except ValueError:
        except Exception:
            raise ValidationError(_('Please enter the date in "Y-m-d" format.\n You entered %s.')%(value))
        query = """SELECT id FROM 
                    (SELECT *,  
                        CASE 
                            WHEN CURRENT_DATE = DATE(join_date + DATE_TRUNC('YEAR', AGE(join_date))) THEN DATE((join_date + DATE_TRUNC('YEAR', AGE(join_date))))
                            ELSE DATE(join_date + DATE_TRUNC('YEAR', AGE(join_date)) + INTERVAL '1 YEAR')
                        END AS anniversary
                FROM hr_employee) aniv
                WHERE 
                anniversary %s '%s';""" % \
                (str(operator), str(value))
        #self.env.cr.execute(query, (value,))
        self.env.cr.execute(query)
        ids = [t[0] for t in self.env.cr.fetchall()]
        return [('id', 'in', ids)]
        #return [('id', '=', '0')]
        #return [(1, '=', 1)]
    
    @api.multi
    def _write_resource_calendar(self):   
        for employee in self:
            if employee.calendar_id:
                self.env.cr.execute("""UPDATE resource_resource SET calendar_id = %d WHERE id = %d""" % (employee.calendar_id.id, employee.resource_id.id))
    
    @api.multi
    @api.depends('contract_ids', 'contract_ids.resource_calendar_id')
    def _compute_calendar(self):
        for employee in self:        
            calendar_id = self.env['resource.calendar']
            if employee.contract_id:
                calendar_id |= employee.contract_id.resource_calendar_id
            employee.calendar_id = calendar_id
            employee._write_resource_calendar()
    
    @api.multi
    def _inverse_calendar(self):   
        for employee in self:        
            calendar_id = self.env['resource.calendar']
            if employee.calendar_id:
                calendar_id |= employee.calendar_id
            employee.resource_id.calendar_id = calendar_id
            
    
    current_year_anniversary_date = fields.Date(string='Current Year Anniversary Date', readonly=True, compute='_compute_anniv_dates', search='_search_current_year_anniversary_date')
    anniversary_date = fields.Date(string='Anniversary Date', readonly=True, compute='_compute_anniv_dates', search='_search_anniversary_date')
    first_anniversary_date = fields.Date(string='First Anniversary Date', readonly=True, compute='_compute_anniv_dates')
    last_anniversary_date = fields.Date(string='Last Anniversary Date', readonly=True, compute='_compute_anniv_dates')
    last_anniversary_start_date = fields.Date(string='Last Anniversary Start Date', readonly=True, compute='_compute_anniv_dates')
    last_anniversary_end_date = fields.Date(string='Last Anniversary End Date', readonly=True, compute='_compute_anniv_dates')
    section_id = fields.Many2one('hr.section', string="Section")    
    coach = fields.Boolean(string='Is a Supervisor')
    coach_id = fields.Many2one(string='Supervisor')    
    identification_id = fields.Char(string='Code')
    company_id = fields.Many2one('res.company', related='resource_id.company_id', store=True)
    user_id = fields.Many2one('res.users', related='resource_id.user_id', store=True)
    
    grade_id = fields.Many2one('hr.grade', string="Grade")
    join_date = fields.Date('Join Date')
    
    num_of_years = fields.Integer(string='Number of Years', readonly=True, compute='_compute_dates')
    num_of_months = fields.Integer(string='Number of Months', readonly=True, compute='_compute_dates')
    age = fields.Integer(string='Age', readonly=True, compute='_compute_dates')
    
    
    
    fingerprint_id = fields.Char('Fingerprint ID')
    attendance_lines = fields.One2many('hr.attendance', 'employee_id', 'Attendances')
    #user_company_id = fields.Many2one('res.company', related='user_id.company_id', string='User Company', readonly=True)
    
    blood_group = fields.Selection([('a+', 'A+ve'), 
                                    ('b+', 'B+ve'), 
                                    ('o+', 'O+ve'), 
                                    ('ab+', 'AB+ve'),
                                    ('a-', 'A-ve'), 
                                    ('b-', 'B-ve'), 
                                    ('o-', 'O-ve'), 
                                    ('ab-', 'AB-ve')], 'Blood Group')
    
    title = fields.Many2one('res.partner.title', 'Title')
    religion_id = fields.Many2one('res.religion', 'Religion')
    employee_type_id = fields.Many2one('hr.employee.type', 'Employee Type')
    
    emergency_contact_lines = fields.One2many('hr.emergency.contact.line', 'employee_id', 'Emergency Contact')
    #employee_qualification_lines = fields.One2many('hr.qualification.line', 'employee_id', 'Qualification')
    employee_dependents_lines = fields.One2many('hr.dependents.line', 'employee_id', 'Dependents')
    
    nick_name = fields.Char('Nick Name')
    on_hold = fields.Boolean('On Hold')
    department_code = fields.Char(related='department_id.code', store=True, string='Department Code')
    designation_code = fields.Char(related='job_id.code', store=True, string='Designation Code')
    last_work_date = fields.Date('Last Day of work')
    payment_mode = fields.Selection([('bank', 'Bank'), ('check', 'Cheque'), ('cash', 'Cash')], 'Payment Method')
    
    permit_no = fields.Char('Work Permit No')
    visa_no = fields.Char('Visa No')
    visa_expire = fields.Date('Visa Expire Date')
    visa_type_id = fields.Many2one('hr.visa.type', 'Visa Type')
    
    emirate_id = fields.Char(string='Emirate ID No')
    emirate_expire = fields.Date('Emirate ID Expire Date')
    passport_expire = fields.Date('Passport Expire Date')
    healthcard_id = fields.Char(string='Health Card No')
    healthcard_expire = fields.Date('Health Card Expire Date')    
    fire_safety_id = fields.Char(string='Fire & Safety Certificate No')
    fire_safety_expire = fields.Date(string='Fire & Safety Expire Date')
    hazmat_id = fields.Char('HAZMAT Certificate No')
    hazmat_expire = fields.Date('HAZMAT Expire Date') 
    calendar_id = fields.Many2one("resource.calendar", string='Working Time', compute='_compute_calendar', inverse='_inverse_calendar', store=True, readonly=True, help="Define the schedule of resource")
    
    exclude_late_signin = fields.Boolean(string='Exclude Late Sign In', default=False)
    exclude_late_signout = fields.Boolean(string='Exclude Late Sign Out', default=False) 
    exclude_absent = fields.Boolean(string='Exclude Absent', default=False)
    
    _sql_constraints = [
        ('identification_company_uniq', 'unique (identification_id, company_id)', 'The code (identification no) of the employee must be unique per company!'),
        ('fingerprint_company_id_uniq', 'unique(fingerprint_id, company_id)', 'The Fingerprint ID of the employee must be unique per company!'),
        ('user_id_uniq', 'unique(user_id)', 'The Related User ID of the employee must be unique per record!'),
    ]
    
    @api.multi
    @api.constrains('user_id', 'company_id')
    def _check_usercompany_empcompany(self):       
        for employee in self:
            user = employee.user_id
            if user and user.company_id != employee.company_id:
                raise ValidationError(_('The company of related user and company of employee should be same!'))
    

    @api.onchange('gender')
    def onchange_gender(self):
        gender = self.gender
        title = False
        if gender and not self.title:
            shortcut = []
            if gender == 'male':
                shortcut = [('shortcut','=', 'Mr.')]
            elif gender == 'female':
                shortcut = [('shortcut','=', 'Miss')]
            elif gender == 'Other':
                shortcut = [('shortcut','=', 'Other')]                
            title = self.env['res.partner.title'].search(shortcut, limit=1, order='id desc')
            if title:
                self.title = title.id
                
class ResourceResource(models.Model):
    _inherit = "resource.resource"
    
    #company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get())
    #calendar_id = fields.Many2one("resource.calendar", string='Working Time', help="Define the schedule of resource")
    #employee_ids = fields.One2many('hr.employee', 'resource_id', string='Employees')
    
    

class HrReligion(models.Model):    
    _name = "res.religion"
         
    name = fields.Char('Name', required=True)
    
class HrEmployeeRelation(models.Model):    
    _name = "hr.employee.relation"
    _order = "id desc"
        
    name = fields.Char('Name', required=True)

class HrEmployeeType(models.Model):    
    _name = "hr.employee.type"
    _order = "name"
    
    name = fields.Char('Name', required=True)
    type = fields.Selection([('full_time', 'Full Time'), 
                             ('part_time', 'Part Time'), 
                             ('temp', 'Temporary')], 'Type', required=True, default='full_time')


class VisaType(models.Model):
    _name = 'hr.visa.type'
    _description = 'Visa Type'
    _order = 'sequence, id'

    name = fields.Char(string='Visa Type', required=True)
    sequence = fields.Integer(default=10)


class HrEmergencyContactLine(models.Model):
    _name = "hr.emergency.contact.line"
    _order = "id desc"
        
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    relation = fields.Many2one('hr.employee.relation', 'Relation')
    country_id = fields.Many2one('res.country', 'Country')
    phone = fields.Char('Phone')
    email = fields.Char('Email')

class exam_type(models.Model):
    _name = "exam.type"
    _order = "id desc"
        
    name = fields.Char('Name', required=True)
    
class qualification_university(models.Model):    
    _name = "qualification.university"
    _order = "id desc"
    
    name = fields.Char('Name', required=True)
    
class employee_qulaification_line(models.Model):
    _name = "hr.qualification.line"
    _order = "id desc"
    
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, ondelete='cascade')
    name = fields.Char('Course', required=True)
    exam_type = fields.Many2one('exam.type', 'Exam Type')
    university_id = fields.Many2one('qualification.university', 'University')
    discipline = fields.Char('Discipline')
    year = fields.Char('Year To Experience')
    certificate_att = fields.Binary('Certificate Attachement')
    
class employee_dependents_line(models.Model):    
    _name = "hr.dependents.line"
    _order = "id desc"
    
    @api.multi
    @api.depends('dob')
    def _get_age_from_dob(self):        
        for record in self:
            age = 0
            if record.dob:
                today = datetime.now()
                dob = datetime.strptime(record.dob, '%Y-%m-%d')
                age = relativedelta(today, dob).years            
            record.update({
                'age': age,
            })
            
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, ondelete='cascade')            
    name = fields.Char('Member Name', required=True)
    relation = fields.Many2one('hr.employee.relation', 'Relation')
    dob = fields.Date('Date of Birth')
    discipline = fields.Char('Discipline')
    mobile = fields.Char('Mobile')
    health_card = fields.Char('Health Card')
    healthcard_expire = fields.Date('Health Card Expiry Date')
    passport_no = fields.Char('Passport No')
    passport_expire = fields.Date('Passport Expiry Date')
    visa_no = fields.Char('Visa No')
    visa_expire = fields.Date('Visa Expiry Date')
    age = fields.Integer(compute=_get_age_from_dob, string='Age')
    emirate_id = fields.Char('Emirates Id')
    emirate_expire = fields.Date('Emirates Id Expiry Date')
    ticket_allowed = fields.Boolean('Ticket Allowed')
    study = fields.Selection([('in_uae','In UAE'),('out_uae','Outside UAE')],'Studying')

class HrSection(models.Model):
    _name = 'hr.section'
    _description = 'Section'
    _order = 'sequence, id'

    name = fields.Char(string='Section', required=True)
    sequence = fields.Integer(default=10)
    
    
