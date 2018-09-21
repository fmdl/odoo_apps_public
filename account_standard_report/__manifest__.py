# -*- coding: utf-8 -*-

{
    'name': 'Standard Accounting Report',
    'version': '11.0.1.2.2',
    'category': 'Accounting',
    'author': 'Florent de Labarre',
    'summary': 'Standard Accounting Report',
    'website': 'https://github.com/fmdl',
    'depends': ['account', 'report_xlsx'],
    'data': [
        'data/report_paperformat.xml',
        'data/data_account_standard_report.xml',
        'data/res_currency_data.xml',
        'report/report_account_standard_report.xml',
        'views/account_view.xml',
        'views/account_standard.xml',
        'views/res_currency_views.xml',
        'wizard/account_standard_report_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'price': 0.0,
    'currency': 'EUR',
    'images': ['images/main_screenshot.png'],
}
