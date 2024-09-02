from typing import NamedTuple
from enum import Enum


# --
# Fragments are the main wait to define the position (and span)
# of something within the source code.
class Fragment(NamedTuple):
    """Defines an offset/length within a given text file."""

    path: str
    offset: int
    length: int
    line: int
    column: int
    text: str | None = None


# Attributes
"""
Constant
"""

# Types

# TODO: Semantically we should have two things:
# - Reference
# - Definition
#
# and then Symbols which are things that have name. Values are things with
# no name, that can be bound to a name (symbol).
#
# Some things are logical, ie. they have a label (human readable description),
# but not a name.
"""
Symbol
    Variable
        Global
        Local
    Keyword
        Modifier
        Operator
    Macro
    Type
    Query (SQL)
    Definition?
        Error
        Exception
        Event
    Binding
        Parameter
        Attribute
        ClassAttribute
        Field
        Option (Command)
        Setting
        Shortcut
    Function
        Builtin
        Delegate?
        Procedure
        Subroutine
        Method
            Constructor
            Destructor
            Accessor
                Getter
                Setter
        ClassMethod
    Command
Structure
    Package (Logical)
        Section
        Library
        Framework
        Component
        Extension
        Plugin
        Provider
        Service
        Test
    Namespace
        Module
    Struct
    Union
    Record
    Class
        Mixin
    Interface
        Protocol
    Enum
    Context
Value
    Element
    Environment
    Resource
    Statement
    Style
    Literal
        String
        Number
            Integer
            Floating
        Collection
            Array
            Tuple
            Map
            Set
    Reference
    Object
        Instance
Meta
    Annotation
    Abstract
    Filter
    Tag
    Hook
    Category
Physical
    File
"""


# NOTE: This is from <https://kapeli.com/docsets>
class SymbolType(Enum):
    Annotation = "Ann"
    Attribute = "Atr"
    Binding = "Bnd"
    Builtin = "Blt"
    Callback = "Cal"
    Category = "Cat"
    Class = "Cls"
    Command = "Cmd"
    Component = "Cmp"
    Constant = "Cst"
    Constructor = "Ctor"
    Delegate = "Del"
    Directive = "Dir"
    Element = "Ele"
    Enum = "Enm"
    Environment = "Env"
    Error = "Err"
    Event = "Evt"
    Exception = "Exc"
    Extension = "Ext"
    Field = "Fld"
    File = "File"
    Filter = "Flt"
    Framework = "Frm"
    Function = "Fun"
    Global = "Glb"
    Hook = "Hck"
    Instance = "Ins"
    Interface = "Int"
    Keyword = "Kwd"
    Library = "Lib"
    Literal = "Ltl"
    Macro = "Mcr"
    Method = "Mtd"
    Mixin = "Mxn"
    Modifier = "Mod"
    Module = "Mdl"
    Namespace = "Nsp"
    Object = "Obj"
    Operator = "Opr"
    Option = "Opt"
    Package = "Pkg"
    Parameter = "Prm"
    Plugin = "Pgn"
    Procedure = "Prc"
    Property = "Prp"
    Protocol = "Ptl"
    Provider = "Prv"
    Query = "Qry"
    Record = "Rcd"
    Resource = "Rsc"
    Section = "Sec"
    Service = "Svc"
    Setting = "Stg"
    Shortcut = "Sct"
    Statement = "Stm"
    Struct = "Str"
    Style = "Sty"
    Subroutine = "Sub"
    Tag = "Tag"
    Test = "Tst"
    Trait = "Trt"
    Type = "Typ"
    Union = "Unn"
    Value = "Val"
    Variable = "Var"


# EOF
