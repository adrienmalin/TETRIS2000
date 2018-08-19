# -*- coding: utf-8 -*-
"""
    Class decorators:

    @propertize buids derived classes
    with a properties for each attribute with accessors
    
    @convert_attributes_name buids derived classes
    with attributes name converted by a function

    Accessors are found among the class's methods (its callable attributes)
    if the method's name start with getters_prefix or setters_prefix.
    If getters_prefix is "", creates property for each method named "method_name"
    only if a setter named "setters_prefix"+"method_name" is found and vice_versa.
    Attributes are named by their accessors' name minus the prefix.
    You can use @rename_attributes(snake_case) to rename all class' attributes
    
    :Example:
        
    >>> from propertize import propertize, snake_case
    >>> class AccessorsClass:
    ...    def __init__(self):
    ...        self._private_attribute = 0
    ...    def getAttribute(self):
    ...        return self._private_attribute
    ...    def setAttribute(self, value):
    ...        self._private_attribute = value
    ...
    >>> @propertize("get", "set")
    ... @rename_attributes(snake_case)
    ... class PropertiesClass(AccessorsClass): pass
    ...
    >>> instance = PropertiesClass()
    >>> instance.attribute = 1
    >>> instance.attribute
    1
"""

from .convert_string import snake_case
from .rename_attributes import rename_attributes
from .propertize import propertize
