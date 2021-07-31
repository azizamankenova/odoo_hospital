# -*- coding: utf-8 -*-
import pytz
from lxml import etree
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _order = "appointment_date desc"

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
    #                     submenu=False):
    #     result = super(HospitalAppointment, self).fields_view_get(view_id,
    #                                                               view_type,
    #                                                               toolbar=toolbar,
    #                                                               submenu=submenu)
    #
    #     doc = etree.XML(result['arch'])
    #     # print("doc", doc)
    #     # for elem in doc.xpath("//field[@name='appointment_date']"):
    #     #     doc.remove(elem)
    #     # result['arch'] = doc
    #     return result

    def delete_lines(self):
        for rec in self:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            time_in_timezone = pytz.utc.localize(rec.appointment_datetime).astimezone(user_tz)
            # print("Time in UTC -->", rec.appointment_datetime)
            # print("Time in Users Timezone -->", time_in_timezone)
            rec.appointment_lines = [(5, 0, 0)]

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    @api.model
    def create(self, vals):
        # overriding the create method to add the sequence
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or _('New')
            result = super(HospitalAppointment, self).create(vals)
            return result

    def write(self, vals):
        # overriding the write method of appointment model
        res = super(HospitalAppointment, self).write(vals)
        # print("Test write function")
        # do as per the need
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            return {'domain': {'order_id': [('partner_id', '=', rec.partner_id.id)]}}

    @api.model
    def default_get(self, fields):
        res = super(HospitalAppointment, self).default_get(fields)
        print("test......")
        res['patient_id'] = 1
        res['notes'] = 'please like the video'
        return res

    # def _get_default_note(self):
    #     return 2

    name = fields.Char(string='Appointment ID', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True)
    # patient_id = fields.Many2one('hospital.patient', string='Patient', required=True, default=_get_default_note)
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor')
    patient_age = fields.Integer('Age', related='patient_id.patient_age')
    notes = fields.Text(string="Registration Note")
    doctor_note = fields.Text(string="Note", track_visibility='onchange')
    appointment_lines = fields.One2many('hospital.appointment.lines', 'appointment_id', string='Appointment Lines')
    pharmacy_note = fields.Text(string="Note", track_visibility='always')
    appointment_date = fields.Date(string='Date')
    appointment_datetime = fields.Datetime(string='Date Time')
    partner_id = fields.Many2one('res.partner', string="Customer")
    order_id = fields.Many2one('sale.order', string="Sale Order")
    amount = fields.Float(string="Total Amount")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, default='draft')


class HospitalAppointmentLines(models.Model):
    _name = 'hospital.appointment.lines'
    _description = 'Appointment Lines'

    product_id = fields.Many2one('product.product', string='Medicine')
    product_qty = fields.Integer(string="Quantity")
    sequence = fields.Integer(string="Sequence")
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment ID')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")