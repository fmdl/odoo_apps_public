# -*- coding: utf-8 -*-

{
    'name': 'OVH SMS Endpoint',
    'version': '2.0',
    'license': 'AGPL-3',
    'depends': ['sms', ],
    'author': 'Florent de Labarre',
    'website': 'https://github.com/fmdl',
    'category': 'crm',
    'external_dependencies': {'python': ['ovh'], },
    'data': ['views/sms_views.xml', 'data/data.xml'],
    'installable': True,
    'price': 0.0,
    'currency': 'EUR'
    'images': ['images/main_screenshot.png']
}
