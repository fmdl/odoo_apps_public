# coding: utf-8

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class IapAccount(models.Model):
    _inherit = 'iap.account'

    ovh_endpoint = fields.Char('End Point', default='ovh-eu')
    ovh_application_key = fields.Char('Application key')
    ovh_application_secret = fields.Char('Application secret')
    ovh_consumer_key = fields.Char('Consumer key')
    ovh_sms_account = fields.Char('SMS account')
    ovh_sms_api_user = fields.Char('SMS API user', help='It can be empty if you do not use OVH API User')
    ovh_sender = fields.Char('Sender')
