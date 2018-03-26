# -*- coding: utf-8 -*-

{
    'name': 'Standard Accounting Report',
    'version': '9.0.1.0.1',
    'category': 'Accounting & Finance',
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
<<<<<<< HEAD
    'price': 0,
=======
    'price': 0.0,
>>>>>>> d5a9e006cb30ba2e4f224fb2ba69fc564bc66722
    'currency': 'EUR',
    'installable': True,
    'images': ['images/main_screenshot.png'],
}
