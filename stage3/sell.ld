ENTRY(ps_choose)
SECTIONS { . = 0x08a0a518; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }
