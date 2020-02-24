# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(cr, registry):
    """ Add region to address format """

    query = """
        UPDATE res_country
        SET address_format = replace(
        address_format,
        E'%(country_name)s',
        E'%(region_name)s\n%(country_name)s'
        )
    """
    cr.execute(query)


def uninstall_hook(cr, registry):
    """ Remove region from address format """
    # Remove %(region)s\n from address_format
    query = """
        UPDATE res_country
        SET address_format = replace(
        address_format,
        E'%(region_name)s\n',
        ''
        )
    """
    cr.execute(query)

    # Remove %(region)s from address_format
    query = """
        UPDATE res_country
        SET address_format = replace(
        address_format,
        E'%(region_name)s',
        ''
        )
    """
    cr.execute(query)
