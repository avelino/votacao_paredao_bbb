"""
This application has debug-related functions and views. It is responsible for the error handling middleware and templates,
for example errors 404 and 500.
    
Traceback reports sent by e-mail are also a function of this application
"""

# Registered templates
from london.apps.themes.registration import register_template
register_template("error_404", mirroring="debug/error_404.html")
register_template("error_500", mirroring="debug/error_500.html")
register_template("error_other", mirroring="debug/error_other.html")
register_template("default_error_404", mirroring="debug/default_error_404.html")
register_template("default_error_500", mirroring="debug/default_error_500.html")