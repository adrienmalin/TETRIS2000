# -*- coding: utf-8 -*-
"""
    Class decorator building derived classes
    with all attributes renamed by a function
"""


def rename_attributes(convert_function):
    """
            :param function_to_convert_name: function used to convert attributes' names
            :type function_to_convert_name: callable
            :return: a derived class with renamed attributes
            :return type: type
    """

    def _rename_attributes(cls):
        if not convert_function: return cls
        
        class ConvertedCase(cls):
            pass

        for attribute_name in dir(cls):
            try:
                attribute = getattr(cls, attribute_name)
            except AttributeError:
                pass
            else:
                new_name = convert_function(attribute_name)
                if new_name != attribute_name:
                    setattr(ConvertedCase, new_name, attribute)
                
        return ConvertedCase
    
    return _rename_attributes
