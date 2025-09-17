# MIOC verilog make file
#
#

#build ?= rtl

#ifneq ($(filter $(build),rtl nmos xilinx),$(build))
ifneq ($(filter $(build),rtl nmos),$(build))
  $(error Invalid build="$(build)". Must be rtl, or nmos)
endif

.PHONY: help
help:
	@echo "Usage: make [run|waves|clean|check] [build=rtl|nmos]"
	@echo ""
	@echo "Examples:"
	@echo "  make run   build=[rtl|nmos]"
	@echo "  make check build=nmos"
	@echo "  make waves build=rtl"

# Require test=... for real goals (not help/clean) only
ifneq ($(strip $(MAKECMDGOALS)),)
  NEED_TEST := $(filter-out help clean,$(MAKECMDGOALS))
  ifneq ($(NEED_TEST),)
    ifeq ($(strip $(build)),)
      $(error Missing required variable: build. Try: make help)
    endif
  endif
endif

# ---------- your variables ----------
COMP  = $(shell which iverilog)
RUN   = $(shell which vvp)


# Define variables
#
CWD = $(shell pwd)

RM = /usr/bin/rm
MD = /usr/bin/mkdir

V_SRC = $(shell ls src/*.v | grep "$(build)" | grep -v "testbench"  2>/dev/null)

build : clean $(V_SRC) 
	$(COMP) -v $(V_SRC) ./src/testbench_$(build).v

run : build
	$(RUN) a.out

waves: run
	gtkwave waves.vcd waves.gtkw

# Clean
#
clean : 
	$(RM) -f ./DATA_OUT/*.*
	$(RM) -f a.out waves.vcd *.xcf

# Remove builtin rules
#
.SUFFIXES:

.SECONDARY:
