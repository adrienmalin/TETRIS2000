# -*- coding: utf-8 -*-
from collections import defaultdict

"""
    Class decorator building derived classes
    with a properties for each hidden attribute with accessors
"""

def propertize(
        getters_prefix = "get_",
        setters_prefix = "set_"
    ):
    """
        :param getters_prefix: methods starting with this prefix will be considered as getters
        :type getters_prefix: str
        :param setters_prefix: methods starting with this prefix will be considered as setters
        :type setters_prefix: str
        :return: a derived class with a properties for each attribute with accessors
        :return type: type
    """
    
    def _propertize(cls):
        if not getters_prefix and not setters_prefix: return cls

        properties_accessors = defaultdict(dict)
        for method_name in dir(cls):
            for accessor_type, prefix in ("getter", getters_prefix), ("setter", setters_prefix):
                if method_name.startswith(prefix):
                    try:
                        method = getattr(cls, method_name)
                    except AttributeError:
                        pass
                    else:
                        if callable(method):
                            property_name = method_name[len(prefix):]
                            properties_accessors[property_name][accessor_type] = method
        
        class propertizeClass(cls):
            pass
        
        for property_name, accessors in properties_accessors.items():
            getter = accessors.get("getter", None)
            setter = accessors.get("setter", None)
            if (getters_prefix or setter) and (setters_prefix or getter):
                setattr(propertizeClass, property_name, property(getter, setter))
                
        return propertizeClass
    
    return _propertize
