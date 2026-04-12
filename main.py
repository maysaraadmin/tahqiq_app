import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTranslator, QLocale, Qt
from views.main_window import MainWindow
from config import config

def setup_application_style(app):
    """Safely load application styles with path validation"""
    try:
        # Set RTL layout for Arabic support
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Validate path to prevent path traversal
        styles_file = config.STYLES_FILE
        if not styles_file.exists():
            return
        
        # Ensure the file is within the expected directory
        try:
            styles_file.resolve().relative_to(config.BASE_DIR)
        except ValueError:
            # Path traversal attempt detected
            config.setup_logging().warning(f"Path traversal attempt: {styles_file}")
            return
        
        # Load styles
        with open(styles_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            config.setup_logging().info("Application styles loaded successfully")
    except Exception as e:
        config.setup_logging().error(f"Failed to load styles: {e}")
        # Continue without styles - not critical

def setup_translation(app):
    """Setup Arabic translation support"""
    try:
        translator = QTranslator()
        locale = QLocale.system().name()
        
        # Try to load translation file (optional)
        translations_dir = str(config.BASE_DIR / "translations")
        if translator.load(locale, translations_dir):
            app.installTranslator(translator)
            config.setup_logging().info(f"Translation loaded for locale: {locale}")
    except Exception as e:
        config.setup_logging().warning(f"Failed to load translation: {e}")
        # Continue without translation - not critical

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = config.setup_logging()
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show user-friendly error message
    QMessageBox.critical(None, "خطأ غير متوقع", 
                        f"حدث خطأ غير متوقع:\n{str(exc_value)}\n\nتم حفظ التفاصيل في ملف السجل.")

def run_migrations():
    """Run database migrations"""
    logger = config.setup_logging()
    try:
        from migrations.migration_manager import migration_manager
        logger.info("Running database migrations...")
        success = migration_manager.migrate_up()
        if success:
            logger.info("Database migrations completed successfully")
        else:
            logger.error("Database migrations failed")
            return False
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    return True

def main():
    # Setup logging first
    logger = config.setup_logging()
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    
    # Setup exception handling
    sys.excepthook = handle_exception
    
    # Run database migrations (temporarily disabled)
    # if not run_migrations():
    #     QMessageBox.critical(None, "خطأ في قاعدة البيانات", 
    #                         "فشل تشغيل ترحيلات قاعدة البيانات. راجع ملف السجل للتفاصيل.")
    #     sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    
    # Setup application features
    setup_translation(app)
    setup_application_style(app)
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        logger.info("Application started successfully")
        
        # Run application
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        QMessageBox.critical(None, "خطأ في التشغيل", 
                            f"فشل تشغيل التطبيق:\n{str(e)}")
        sys.exit(1)
    finally:
        # Cleanup - use existing singleton instance
        try:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager._instance
            if db_manager:
                db_manager.close_all()
                logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # Additional cleanup
        try:
            logger.info("Application shutdown complete")
        except Exception as e:
            pass  # Ignore logging errors during shutdown

if __name__ == "__main__":
    main()
