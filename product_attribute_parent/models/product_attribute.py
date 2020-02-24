from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ProductAttribute(models.Model):
    _inherit = "product.attribute"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('product.attribute', 'Parent Attribute', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('product.attribute', 'parent_id', 'Child Attributes')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for attribute in self:
            if attribute.parent_id:
                attribute.complete_name = '%s / %s' % (attribute.parent_id.complete_name, attribute.name)
            else:
                attribute.complete_name = attribute.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    @api.multi
    def name_get(self):
        return [(value.id, "%s" % (value.complete_name)) for value in self]


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    @api.multi
    def name_get(self):
        if not self._context.get('show_attribute', True):  # TDE FIXME: not used
            return super(ProductAttributeValue, self).name_get()
        return [(value.id, "%s: %s" % (value.attribute_id.complete_name, value.name)) for value in self]
