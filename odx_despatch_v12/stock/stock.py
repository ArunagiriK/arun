# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import Warning

# class Procurment(models.Model):
#     _inherit = 'procurement.order'
#     od_carton_no = fields.Char(string="Carton")
#     od_packaging_no = fields.Char(string="Packaging")


class StockMove(models.Model):
    _inherit = 'stock.move' 
    od_carton_no = fields.Char(string="Carton")
    od_packaging_no = fields.Char(string="Packaging")
    
    def _get_new_picking_values(self):
        """ Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited. """
        res = super(StockMove,self)._get_new_picking_values()
        od_deliveryloc_id = self.group_id and self.group_id.od_deliveryloc_id and self.group_id.od_deliveryloc_id.id or False
        
        od_carton_no = self.group_id and self.group_id.od_carton_no
        od_packaging_no = self.group_id and self.group_id.od_packaging_no
        od_client_order_ref = self.group_id and self.group_id.od_client_order_ref
        od_incoterm = self.group_id and self.group_id.od_incoterm and self.group_id.od_incoterm.id or False
        res.update({'od_carton_no':od_carton_no,
                    'od_packaging_no':od_packaging_no,
                    'od_client_order_ref':od_client_order_ref,
                    'od_incoterm':od_incoterm,
                    'od_deliveryloc_id':od_deliveryloc_id
                    
                    })
        return res
   

class Picking(models.Model):
    _inherit = 'stock.picking'
    move_lines2 = fields.One2many('stock.move','picking_id',string="Packaging")
    od_carton_no = fields.Char(string="Carton")
    od_packaging_no = fields.Char(string="Packaging")
    od_client_order_ref = fields.Char(string="Client Order Ref")
    od_incoterm = fields.Many2one('stock.incoterms',string="Incoterm")
    od_deliveryloc_id = fields.Many2one('od.delivery.loc',string='Delivery Location')
    od_cleared = fields.Boolean(string="Cleared")

    def od_prepare_invoice_vals(self):
        res = super(Picking,self).od_prepare_invoice_vals()
        partner = self.partner_id
        od_group_id = partner.od_group_id and  partner.od_group_id.id
        od_type_id = partner.od_type_id and  partner.od_type_id.id
        od_category_id = partner.od_category_id and  partner.od_category_id.id
        od_area_id = partner.od_area_id and  partner.od_area_id.id
        res.update({'od_group_id':od_group_id,
                    'od_type_id':od_type_id,
                    'od_category_id':od_category_id,
                    'od_area_id':od_area_id
                    })
        return res