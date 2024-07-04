import enum
import logging
from functools import partial, wraps
from typing import Callable, Dict, Type, TypeVar

from fastapi import Header, Request
from pyparsing import Any

from translation.language import Language

_T = TypeVar("_T")
_translators:Dict[Type, Dict[Language, Callable[[_T],_T]]] = {}

def register_translator(cls:Type[Any], language:Language):
    def decorator(func:Callable[[_T],_T]):  
        if cls not in _translators.keys():
            _translators[cls] = {}

        if language in _translators[cls].keys():
            raise KeyError()
        
        _translators[cls][language] = func
        return func
    return decorator

def _get_translator(cls:Type[Any], language:Language):
    return _translators[cls][language]

def _no_translator(e:Any):
    return e

class UnsupportedLanguage(Exception):
    pass

def _get_accepted_language(accepted_language:str):
    language = accepted_language
    language = language.split("-")[0].lower()
    try:
        return Language(language)
    except Exception as e:
        raise UnsupportedLanguage from e

# fastapi dependency
def translate(
    accepted_language:str=Header(
        default="en",
        alias="Accept-Language",
        convert_underscores=False,
        include_in_schema=False
    )):
    """
    fastapi dependency that will return a function if possible to translate
    """

    try:
        language = _get_accepted_language(accepted_language)
    except UnsupportedLanguage:
        return _no_translator
    
    return partial(_translate_element, language)

def _translate_element(element:Any, language:Language):
    try:
        _get_translator(type(element), language)
    except KeyError:
        logging.info(f"no translator for cls:{type(element).__name__} and language:{language}")
        return _no_translator
