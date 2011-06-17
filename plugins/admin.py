"""
    Very simple plugin to only let admins run functions. Need to update
    this to be more secure.
"""

admins = ['Reisen']

def authorized(user):
    if user in admins:
        return True

    return False
