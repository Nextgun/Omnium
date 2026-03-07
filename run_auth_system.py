"""
Simple script to run the UserInterface for the auth system.
Just run this file to test the registration and login system.
"""

from registration.auth_system import UserInterface

if __name__ == "__main__":
    # Create the user interface
    ui = UserInterface()
    
    # Run the application
    ui.run()
