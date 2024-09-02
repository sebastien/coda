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
