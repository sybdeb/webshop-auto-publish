"""Module installation and uninstallation hooks"""
import logging

_logger = logging.getLogger(__name__)

def uninstall_hook(env):
    """Clean up all module data when uninstalling"""
    _logger.info('Running uninstall hook for webshop_product_creator')
    
    try:
        # Remove actions
        env.cr.execute("""
            DELETE FROM ir_act_window 
            WHERE res_model IN ('product.bulk.create', 'product.quick.create', 'product.import.job')
        """)
        _logger.info('Removed actions')
        
        # Remove views
        env.cr.execute("""
            DELETE FROM ir_ui_view 
            WHERE model IN ('product.bulk.create', 'product.quick.create', 'product.import.job', 'product.bulk.create.line')
        """)
        _logger.info('Removed views')
        
        # Remove cron jobs
        env.cr.execute("""
            DELETE FROM ir_cron 
            WHERE cron_name LIKE '%Product Import%'
        """)
        _logger.info('Removed cron jobs')
        
        # Remove server actions (needed before model deletion due to FK)
        env.cr.execute("""
            DELETE FROM ir_act_server 
            WHERE model_name IN ('product.import.job')
        """)
        _logger.info('Removed server actions')
        
        # Remove model fields
        env.cr.execute("""
            DELETE FROM ir_model_fields 
            WHERE model IN ('product.bulk.create', 'product.quick.create', 'product.import.job', 'product.bulk.create.line')
        """)
        _logger.info('Removed model fields')
        
        # Remove models
        env.cr.execute("""
            DELETE FROM ir_model 
            WHERE model IN ('product.bulk.create', 'product.quick.create', 'product.import.job', 'product.bulk.create.line')
        """)
        _logger.info('Removed models')
        
        # Remove menu items
        env.cr.execute("""
            DELETE FROM ir_ui_menu 
            WHERE id IN (
                SELECT DISTINCT menu_id 
                FROM ir_model_data 
                WHERE module = 'webshop_product_creator' AND model = 'ir.ui.menu'
            )
        """)
        _logger.info('Removed menu items')
        
        env.cr.commit()
        _logger.info('Uninstall cleanup completed successfully')
        
    except Exception as e:
        _logger.error('Error during uninstall cleanup: %s', e)
        # Don't raise - let uninstall continue even if cleanup fails
