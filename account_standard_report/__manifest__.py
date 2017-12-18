# -*- coding: utf-8 -*-

{
    'name': 'Standard Accounting Report',
    'version': '10.0.1.2.0',
    'category': 'Accounting & Finance',
    'author': 'Florent de Labarre',
    'summary': 'Great Accounting Report - easy to use - Tree View, PDF and Excel mode.',
    'website': 'https://github.com/fmdl',
    'depends': ['account', 'report_xlsx'],
    'data': [
        'data/report_paperformat.xml',
        'data/data_account_standard_report.xml',
        'report/report_account_standard_report.xml',
        'views/account_view.xml',
        'views/account_standard.xml',
        'wizard/account_standard_report_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'images': ['images/main_screenshot.png'],
}
