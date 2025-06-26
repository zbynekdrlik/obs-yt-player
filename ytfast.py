"""
Backward compatibility wrapper for ytfast.py users.
This file simply imports and re-exports all functions from ytplay.py
to maintain compatibility with existing OBS setups.

Users can continue using ytfast.py or migrate to ytplay.py.
Both scripts share the same ytplay_modules directory.
"""

# Import everything from ytplay
from ytplay import *

# Note: This is just a wrapper. All functionality is in ytplay.py and ytplay_modules/
