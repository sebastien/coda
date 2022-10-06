
- Source is parsed for SYMBOLS and BLOCKS
- SYMBOLS can be DECLARED or REFERENCED
- BLOCKS define a logical grouping of things. It can be semantic (class/methods) or syntactic (explicit START/END markers)
- Parsing does not need to make sense of things, it just needs to do


```
BLOCK -[contains]→   BLOCK
^                     |
|                   [references]
|                     |
|                     v
+----[defined in]--- SYMBOL
```

Blocks have types:
- Comment
  - Documentation
- Structure
  - Declaration
