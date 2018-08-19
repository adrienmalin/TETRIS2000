# -*- coding: utf-8 -*-
import re


first_cap_re = re.compile('([^.])([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

def snake_case(s):
    """
    Convert a CamelCase string to snake_case
    """
    
    s1 = first_cap_re.sub(r'\1_\2', s)
    return all_cap_re.sub(r'\1_\2', s1).lower()