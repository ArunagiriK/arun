# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from odoo.exceptions import UserError, ValidationError
import logging
import os
import sys
import requests
import errno
import base64
import tempfile, shutil, os
import camelot
from io import StringIO 
from io import BytesIO
from io import TextIOWrapper
from zipfile import ZipFile
import io
_logger = logging.getLogger(__name__)


try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')



class ImportSalePdf(models.TransientModel):
    _name = 'import.sale.pdf'
    _description = 'Import Sale'
    
    sale_id = fields.Many2one('sale.order','Sale Order')
    pdf_name = fields.Char('Filename')
    file_upload_pdf = fields.Binary('File Upload',attachment=True)
    
    csv_name = fields.Char('Csv File')
    generate_csv = fields.Binary('CSV File')
    
    @api.model
    def default_get(self,fields_lst):
        res = super(ImportSalePdf,self).default_get(fields_lst)
        sale_order_brw = self.env['sale.order'].browse(self._context.get('active_id'))
        res.update({'sale_id':sale_order_brw.id})
        return res


    def find_files(self,filename, search_path):
        result = []
        print('WWWWWWWWWWWWWWWWWWWWWWWWWWWWW',filename,search_path)
        
        for root, dir, files in os.walk(search_path):
            print('FILES:',files)
            for file in files:
                if file.endswith(".zip"):
                   print(file,'$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                   result.append(os.path.join(root, filename))
        return result

    
    def generate_pdf_csv(self):
        file_name = self.pdf_name
        #~ data = self.file_upload_pdf
        #~ data_file = io.StringIO(data.decode("utf-8"))
        
        
        
        encoded_string = self.file_upload_pdf
        decode_string = base64.b64decode(encoded_string)
        temp_path = os.path.expanduser('~')+ '/zip directory' + '/%s'%(file_name)
        with open(temp_path, "wb") as fh:
            fh.write(decode_string)
        
        #~ temp_path = os.path.expanduser('~')+ '/%s'%(file_name)
        #~ shutil.copy2(file_name,temp_path)
        #~ os.chmod(temp_path, 0o444)
        
        pdf = os.path.expanduser('~')+ '/zip directory' + '/%s'%(file_name)
        pdf_file = pdf
        print("SDDDDDDDDDDDDDDDDDDDDDDDDDDd",pdf_file,file_name)
        tables = camelot.read_pdf(pdf_file, pages='all')
        csv_file = pdf_file + '.csv'
        tables.export(csv_file, f='csv', compress=True)
        t=tables
        
        search_file=self.find_files(file_name[:-4] + '.pdf.zip' ,os.path.expanduser('~')+ '/zip directory')
        for line in search_file:
             a = line.split('/')
             file_zip = a[4]
             print(file_zip)
             self.write({'csv_name':file_zip,'generate_csv':file_zip})
             print(self.write({'csv_name':file_zip,'generate_csv':file_zip}))
             print('nnnnnnnnnnnnnnnnnnnnnnnnnnnn',self.csv_name)

              

             
        form_view = self.env.ref('import_sale_order_pdf.view_import_sale_pdf_xml')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'name': 'Fee receipt',
            'res_model': 'import.sale.pdf',
            'view_id': False,
            'views': [(form_view and form_view.id or False, 'form')],
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'nodestroy': True
            }
             #~ with open(temp_path, "rb") as f:
                  #~ bytes = f.write(zip_file)
                  #~ encoded = base64.b64encode(bytes)

                  
             #~ data.write(self.csv_name)
             #~ decode_string = base64.b64decode(encoded_string)
             #~ print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAA',encoded)
        #~pri attachment_dict = {
                            #~ 'name': ''
                            #~ 'datas': self.file_upload_pdf,
                            #~ 'datas_fname': file_name,
                            #~ 'res_model': self._name,
                            #~ 'res_id': self.id,
                            #~ 'type': 'binary',
                        #~ }
        #~ attachment_id = self.env['ir.attachment'].sudo().create(attachment_dict)
            
        
        #~ zip_lst = self.generate_csv
        #~ print('zip_lst',zip_lst)
        #~ tables[0].to_csv(csv_file)
        #~ f = StringIO(csv_file)
        #~ csv_obj=open(csv_file, 'w')
        #~ print(csv_obj,"@@@#@%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        #~ csv_file = self.generate_csv
        #~ print(table,'#################################')
        #~ csv_path = os.path.expanduser('~')+ '/%s'%(csv_file)
        #~ print(csv_path,'*****************************************************')
        #~ with open(csv_file, 'w') as f:
            #~ self.generate_csv = f
            #~ csv_data = base64.b64decode(f)
            #~ data_file = io.StringIO(csv_data.decode("utf-8"))
            #~ data_file.seek(0)
            #~ print()
        #~ print(csv_file.read(),'@@@@@@@@@@@@%$%%%%%%%%%%%%%%%%%%%')
        #~ attachment_value = {
                #~ 'name': 'CSV File',
                #~ 'datas': f.read(),
                #~ 'datas_fname': csv_file,
                #~ 'res_model': self._name,
                #~ 'res_id': self.id,
            #~ }
        #~ attachment_id = self.env['ir.attachment'].sudo().create(attachment_value)
        #~ print('!@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',attachment_id)
        #~ with open(df,'rt')as f:
            #~ data = csv.writer(f, delimiter=",", lineterminator='\n')
        #~ csv = self.generate_cs
            #~ data = self.generate_csv
            #~ print(data)
    
    @api.multi
    def import_zip(self):
        sale_order_brw = self.env['sale.order'].browse(self._context.get('active_id'))
        
        print(sale_order_brw,self._context,"INSIDE ZIPPPPPPPPPPPPPPPPPPPPPPP")
        zip_file = os.path.expanduser('~')+ '/zip directory' + '/%s'%(self.csv_name)
        print(zip_file,'ZZZZZZZZZZZZZIP')
        keys = ['article_no' 'quantity', 'uom','description', 'price', 'tax']
        values = {}
        lst =[]
        with ZipFile(zip_file) as zf:
             print(zf,'ZFZFFFFFFZF')
             for name in zf.namelist():
                 with zf.open(name, 'r') as infile:
                    csv_reader = csv.reader(TextIOWrapper(infile, 'utf-8'))
                    for row in (csv_reader):
                        if len(row) == 16:
                            if len(row)<=5 :
                                continue
                            else:
                                if row[4]== '' or row[4]== 'Article':
                                   continue
                                else:
                                    print(row)
                                    floats=row[8].split()
                                    print(floats)
                                    values = {
                                           'article_no' : row[4],
                                           'quantity' :   floats[0]
                                            
                                    }
                                    lst.append(values)
                        else:
                            if len(row)<=5 :
                                continue
                            else:
                               if row[1]== '' or row[1] == 'Article':
                                  continue
                               else:
                                   floats=row[1].split(' ')
                                   values = {
                                           'article_no' : floats[0],
                                           'quantity' :   row[6]
                                            
                                   }
                                   print("LISSSSSSSSSSSSSSSST",values)
                                   lst.append(values)
                            
        if lst:
           print('LIST:',lst)
           self.create_order_line(lst,sale_order_brw)
                    
                            
                   
 
            
    
    @api.multi
    def import_sol(self):
        keys = ['article_no' 'quantity', 'uom','description', 'price', 'tax']
        #~ try:
       
        csv_data = base64.b64decode(self.generate_csv)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        values = {}
        #~ with open(csv_data, "r") as csv_file:
       
        csv_reader = csv.reader(data_file, delimiter=',')
        #~ next(csv_reader)
        file_reader.extend(csv_reader)
        #~ except Exception:
            #~ raise Warning(_("Please select any file or You have selected invalid file"))
        #~ for line in csv_reader:
             #~ print(line[8],"LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
        for i in range(len(file_reader)):
            field = list(map(str, file_reader[i]))
            values = dict(zip(keys, field))
            floats = [x for x in field[8].split()]
            print(floats[0])
            if values:
                if i == 0:
                    continue
                else:
                    values.update({
                                    'article_no' : field[4],
                                    'quantity' : floats[0]
                                    })
                    res = self.create_order_line(values)
        return res

    @api.multi
    def create_order_line(self,lst,sale_order_brw):
        #~ sale_order_brw = self.env['sale.order'].browse(self._context.get('active_id'))
        sale_order_brw = self.sale_id
        print("SALE:",sale_order_brw)
        for values in lst:
            article=values.get('article_no')
            product_obj_search=self.env['product.product'].search([('article_no',  '=',values['article_no'])])
            print(product_obj_search,'PPPPPPPPPPPPPPPPPPPPPPPPRODUCT')
            print(article,'@@@@@@@@@@@@@@@@@@@@@@@')
            if product_obj_search:
                 product_id= product_obj_search
            else:
              raise Warning(_('%s product is not found".') % (values.get('article_no')))
            if sale_order_brw.state == 'draft':
                print("ORDERLINESSSSSSS:",sale_order_brw)
                order_lines=self.env['sale.order.line'].create({
                                                    'order_id':sale_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':product_id.name,
                                                    'product_uom_qty':values.get('quantity'),
                                                    'product_uom':product_id.uom_id.id,
                                                    'price_unit':product_id.lst_price,
                                                    })
                print(order_lines,'ORDERLINES')
            elif sale_order_brw.state == 'sent':
                 order_lines=self.env['sale.order.line'].create({
                                                    'order_id':sale_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':product_id.name,
                                                    'product_uom_qty':values.get('quantity'),
                                                    'product_uom':product_id.uom_id.id,
                                                    'price_unit':product_id.lst_price,
                                                    })
            elif sale_order_brw.state != 'sent' or sale_order_brw.state != 'draft':
                    raise UserError(_('We cannot import data in validated or confirmed order.'))
