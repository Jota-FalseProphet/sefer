
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# Server UX
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-ux&target_branch=15.0)
[![Pre-commit Status](https://github.com/OCA/server-ux/actions/workflows/pre-commit.yml/badge.svg?branch=15.0)](https://github.com/OCA/server-ux/actions/workflows/pre-commit.yml?query=branch%3A15.0)
[![Build Status](https://github.com/OCA/server-ux/actions/workflows/test.yml/badge.svg?branch=15.0)](https://github.com/OCA/server-ux/actions/workflows/test.yml?query=branch%3A15.0)
[![codecov](https://codecov.io/gh/OCA/server-ux/branch/15.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-ux)
[![Translation Status](https://translation.odoo-community.org/widgets/server-ux-15-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-ux-15-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

Server side features for usability and user experience related.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[announcement](announcement/) | 15.0.2.2.0 |  | Notify internal users about relevant organization stuff
[barcode_action](barcode_action/) | 15.0.1.0.0 |  | Allows to use barcodes as a launcher
[base_archive_date](base_archive_date/) | 15.0.1.0.0 | <a href='https://github.com/GuillemCForgeFlow'><img src='https://github.com/GuillemCForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='GuillemCForgeFlow'/></a> | Adds an archive timestamp and user doing the archiving to all models.
[base_cancel_confirm](base_cancel_confirm/) | 15.0.1.0.0 | <a href='https://github.com/kittiu'><img src='https://github.com/kittiu.png' width='32' height='32' style='border-radius:50%;' alt='kittiu'/></a> | Base Cancel Confirm
[base_custom_filter](base_custom_filter/) | 15.0.1.0.0 | <a href='https://github.com/AshishHirapara'><img src='https://github.com/AshishHirapara.png' width='32' height='32' style='border-radius:50%;' alt='AshishHirapara'/></a> <a href='https://github.com/ForgeFlow'><img src='https://github.com/ForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='ForgeFlow'/></a> | Add custom filters in standard filters and group by dropdowns
[base_duplicate_security_group](base_duplicate_security_group/) | 15.0.1.0.1 | <a href='https://github.com/chienandalu'><img src='https://github.com/chienandalu.png' width='32' height='32' style='border-radius:50%;' alt='chienandalu'/></a> | Adds a security group to restrict which users can copy records
[base_export_manager](base_export_manager/) | 15.0.1.0.3 |  | Manage model export profiles
[base_field_deprecated](base_field_deprecated/) | 15.0.1.0.0 | <a href='https://github.com/GuillemCForgeFlow'><img src='https://github.com/GuillemCForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='GuillemCForgeFlow'/></a> | Adds the deprecated attribute to the Odoo field model.
[base_import_security_group](base_import_security_group/) | 15.0.1.0.1 |  | Group-based permissions for importing CSV files
[base_menu_visibility_restriction](base_menu_visibility_restriction/) | 15.0.1.0.0 | <a href='https://github.com/victoralmau'><img src='https://github.com/victoralmau.png' width='32' height='32' style='border-radius:50%;' alt='victoralmau'/></a> | Restrict (with groups) menu visibilty
[base_multi_branch_company](base_multi_branch_company/) | 15.0.1.0.0 | <a href='https://github.com/Saran440'><img src='https://github.com/Saran440.png' width='32' height='32' style='border-radius:50%;' alt='Saran440'/></a> | Add multi branch of company
[base_optional_quick_create](base_optional_quick_create/) | 15.0.1.0.0 |  | Avoid "quick create" on m2o fields, on a "by model" basis
[base_recurrence](base_recurrence/) | 15.0.1.0.0 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | Allows to define base methods for recurrence computation
[base_revision](base_revision/) | 15.0.1.0.0 |  | Keep track of revised document
[base_search_custom_field_filter](base_search_custom_field_filter/) | 15.0.1.0.1 | <a href='https://github.com/pedrobaeza'><img src='https://github.com/pedrobaeza.png' width='32' height='32' style='border-radius:50%;' alt='pedrobaeza'/></a> | Add custom filters for fields via UI
[base_substate](base_substate/) | 15.0.1.0.1 |  | Base Sub State
[base_technical_features](base_technical_features/) | 15.0.1.1.0 |  | Access to technical features without activating debug mode
[base_tier_validation](base_tier_validation/) | 15.0.1.6.0 | <a href='https://github.com/LoisRForgeFlow'><img src='https://github.com/LoisRForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='LoisRForgeFlow'/></a> | Implement a validation process based on tiers.
[base_tier_validation_formula](base_tier_validation_formula/) | 15.0.1.0.1 |  | Formulas for Base tier validation
[base_tier_validation_forward](base_tier_validation_forward/) | 15.0.1.0.1 | <a href='https://github.com/kittiu'><img src='https://github.com/kittiu.png' width='32' height='32' style='border-radius:50%;' alt='kittiu'/></a> | Forward option for base tiers
[base_tier_validation_report](base_tier_validation_report/) | 15.0.1.0.1 | <a href='https://github.com/kittiu'><img src='https://github.com/kittiu.png' width='32' height='32' style='border-radius:50%;' alt='kittiu'/></a> | Reports related to tier validation
[base_tier_validation_server_action](base_tier_validation_server_action/) | 15.0.1.0.0 | <a href='https://github.com/kittiu'><img src='https://github.com/kittiu.png' width='32' height='32' style='border-radius:50%;' alt='kittiu'/></a> | Add option to call server action when a tier is validated
[base_user_locale](base_user_locale/) | 15.0.1.1.0 |  | User Locale Settings
[base_warn_option](base_warn_option/) | 15.0.1.0.0 | <a href='https://github.com/Shide'><img src='https://github.com/Shide.png' width='32' height='32' style='border-radius:50%;' alt='Shide'/></a> <a href='https://github.com/rafaelbn'><img src='https://github.com/rafaelbn.png' width='32' height='32' style='border-radius:50%;' alt='rafaelbn'/></a> | Add Options to Warn Messages
[chained_swapper](chained_swapper/) | 15.0.1.0.4 |  | Chained Swapper
[date_range](date_range/) | 15.0.1.1.1 | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Manage all kind of date range
[date_range_account](date_range_account/) | 15.0.1.0.0 | <a href='https://github.com/alexis-via'><img src='https://github.com/alexis-via.png' width='32' height='32' style='border-radius:50%;' alt='alexis-via'/></a> | Add Date Range menu entry in Invoicing app
[default_multi_user](default_multi_user/) | 15.0.1.0.1 | <a href='https://github.com/LoisRForgeFlow'><img src='https://github.com/LoisRForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='LoisRForgeFlow'/></a> | Allows to share user-defined defaults among several users.
[document_quick_access](document_quick_access/) | 15.0.1.0.0 | <a href='https://github.com/etobella'><img src='https://github.com/etobella.png' width='32' height='32' style='border-radius:50%;' alt='etobella'/></a> | Document quick access
[document_quick_access_folder_auto_classification](document_quick_access_folder_auto_classification/) | 15.0.1.1.1 | <a href='https://github.com/etobella'><img src='https://github.com/etobella.png' width='32' height='32' style='border-radius:50%;' alt='etobella'/></a> | Auto classification of Documents after reading a QR
[filter_multi_user](filter_multi_user/) | 15.0.1.0.0 | <a href='https://github.com/LoisRForgeFlow'><img src='https://github.com/LoisRForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='LoisRForgeFlow'/></a> | Allows to share user-defined filters filters among several users.
[mass_editing](mass_editing/) | 15.0.1.1.1 |  | Mass Editing
[multi_step_wizard](multi_step_wizard/) | 15.0.1.0.1 |  | Multi-Steps Wizards
[sequence_check_digit](sequence_check_digit/) | 15.0.1.0.1 |  | Adds a check digit on sequences
[sequence_reset_period](sequence_reset_period/) | 15.0.1.0.0 |  | Auto-generate yearly/monthly/weekly/daily sequence period ranges
[template_content_swapper](template_content_swapper/) | 15.0.1.0.0 |  | Template Content Swapper
[web_archive_date](web_archive_date/) | 15.0.1.0.0 | <a href='https://github.com/GuillemCForgeFlow'><img src='https://github.com/GuillemCForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='GuillemCForgeFlow'/></a> | Reflects the Latest Archived Date and Latest Archived by on the record metadata.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
