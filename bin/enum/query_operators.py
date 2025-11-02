from enum import StrEnum
# from typing import Literal

class QueryOperator(StrEnum):
    EQUAL = "$eq"
    NOT_EQUAL = "$ne"
    GREATER_THAN = "$gt"
    GREATER_THAN_OR_EQUAL = "$gte"
    LOWER_THAN = "$lt"
    LOWER_THAN_OR_EQUAL = "$lte"
    IN = "$in"
    NOT_IN = "$nin"
    LIKE = "$like"
    ILIKE = "$ilike"
    STARTS_WITH = "$startswith"
    ENDS_WITH = "$endswith"
    CONTAINS = "$contains"
    CONTAINS_ANY = "$contains_any"
    EMPTY = "$empty"
    HAS_KEYS = "$has_keys"
    HAS_ANY_KEY = "$has_any_key"
    HAS_VALUES = "$has_values"
    HAS_ANY_VALUE = "$has_any_value"

    AND = "$and"
    OR = "$or"

# ExactMatchOperators = Literal[QueryOperator.EQUAL, QueryOperator.NOT_EQUAL]
# StringOperators = Literal[
#     QueryOperator.EQUAL,
#     QueryOperator.NOT_EQUAL,
#     QueryOperator.LIKE,
#     QueryOperator.ILIKE,
#     QueryOperator.IN,
#     QueryOperator.NOT_IN
# ]
# BooleanOperators = Literal[
#     QueryOperator.EQUAL,
#     QueryOperator.NOT_EQUAL
# ]
# NumericOperators = Literal[
#     QueryOperator.EQUAL,
#     QueryOperator.NOT_EQUAL,
#     QueryOperator.GREATER_THAN,
#     QueryOperator.GREATER_THAN_OR_EQUAL,
#     QueryOperator.LOWER_THAN,
#     QueryOperator.LOWER_THAN_OR_EQUAL,
#     QueryOperator.IN,
#     QueryOperator.NOT_IN
# ]
# UuidOperators = Literal[
#     QueryOperator.EQUAL,
#     QueryOperator.NOT_EQUAL,
#     QueryOperator.IN,
#     QueryOperator.NOT_IN
# ]
# ListOperators = Literal[
#     QueryOperator.EQUAL,       
#     QueryOperator.NOT_EQUAL,   
#     QueryOperator.CONTAINS,    
#     QueryOperator.CONTAINS_ANY,
#     QueryOperator.EMPTY        
# ]
# DictOperators = Literal[
#     QueryOperator.EQUAL,     
#     QueryOperator.NOT_EQUAL, 
#     QueryOperator.CONTAINS,  
#     QueryOperator.HAS_KEYS,  
#     QueryOperator.HAS_ANY_KEY
# ]