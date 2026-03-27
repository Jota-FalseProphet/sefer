{
    "name": "CalcuButanito",
    "version": "15.0.1.0",
    "category": "Tools",
    "summary": "A simple functional calculator in Odoo 15",
    "author": "Juan José Perdomo Ortiz, Izan Rubio, Andreu Gilabert",
    "depends": ["web"],
    "data": [
        "views/menu.xml",
        "views/calculator_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "calculator_module/static/src/js/calculator.js",
        ],
    },
    "installable": True,
    "application": True,
}

