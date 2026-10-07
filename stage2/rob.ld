ENTRY(wrap_load)
SECTIONS { . = 0x08a0981c; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }
