# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.exceptions import ValidationError


class ResPartners(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals_list):
        res = super(ResPartners, self).create(vals_list)
        print("yes working")
        return res


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    patient_name = fields.Char(string='Patient Name')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(selection_add=[('om', 'Odoo Mates'), ('odoodev', 'Odoo Dev')])


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Patient Record'
    _rec_name = 'patient_name'

    @api.model
    def test_cron_job(self):
        print("Abcd")

    def name_get(self):
        # name get function for the model executes automatically
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.patient_name, rec.name_seq)))
        return res

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('name_seq', operator, name), ('patient_name', operator, name)]
        return super(HospitalPatient, self).search(domain, limit=limit).name_get()


    def open_patient_appointments(self):
        return {
            'name': _('Appointments'),
            'domain': [('patient_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'hospital.appointment',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_appointment_count(self):
        count = self.env['hospital.appointment'].search_count([('patient_id', '=', self.id)])
        self.appointment_count = count

    @api.onchange('doctor_id')
    def set_doctor_gender(self):
        for rec in self:
            if rec.doctor_id:
                rec.doctor_gender = rec.doctor_id.gender

    def action_send_card(self):
        # sending the patient report to patient via email
        template_id = self.env.ref('om_hospital.patient_card_email_template').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    @api.depends('patient_name')
    def _compute_upper_name(self):
        for rec in self:
            rec.patient_name_upper = rec.patient_name.upper() if rec.patient_name else False

    @api.depends('patient_age')
    def set_age_group(self):
        for rec in self:
            if rec.patient_age:
                if rec.patient_age < 18:
                    rec.age_group = 'minor'
                else:
                    rec.age_group = 'major'

    def _inverse_upper_name(self):
        for rec in self:
            rec.patient_name = rec.patient_name_upper.lower() if rec.patient_name_upper else False

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('hospital.patient.sequence') or _('New')
        result = super(HospitalPatient, self).create(vals)
        return result

    @api.constrains('patient_age')
    def check_age(self):
        for rec in self:
            if rec.patient_age <= 5:
                raise ValidationError(_("The Age Must be greater than 5"))

    def print_report(self):
        return self.env.ref('om_hospital.report_patient_card').report_action(self)

    def print_report_excel(self):
        return self.env.ref('om_hospital.report_patient_card_xlx').report_action(self)

    name = fields.Char(string='Contact Number')
    name_seq = fields.Char(string='Patient ID', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    gender = fields.Selection([
        ('male', 'Male'),
        ('fe_male', 'Female')
    ], default='male', string="Gender")
    age_group = fields.Selection([
        ('major', 'Major'),
        ('minor', 'Minor')
    ], string="Age Group", compute='set_age_group', store=True)
    patient_name = fields.Char(string='Name', required=True, track_visibility="always")
    patient_age = fields.Integer('Age', track_visibility="always", group_operator=False)
    patient_age2 = fields.Float(string="Age2")
    notes = fields.Text(string='Notes')
    image = fields.Binary(string="Image", attachment=True)
    appointment_count = fields.Integer(string='Appointment', compute='get_appointment_count')
    active = fields.Boolean("Active", default=True)
    doctor_id = fields.Many2one('hospital.doctor', string="Doctor")
    email_id = fields.Char(string="Email")
    user_id = fields.Many2one('res.users', string="PRO")
    doctor_gender = fields.Selection([
        ('male', 'Male'),
        ('fe_male', 'Female'),
    ], string="Doctor Gender")
    patient_name_upper = fields.Char(compute='_compute_upper_name', inverse='_inverse_upper_name')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id)

