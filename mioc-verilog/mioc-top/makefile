# ---------- CLI args & defaults ----------
.DEFAULT_GOAL := help

build ?= rtl

#ifneq ($(filter $(build),rtl nmos xilinx),$(build))
ifneq ($(filter $(build),rtl nmos),$(build))
  $(error Invalid build="$(build)". Must be rtl, or nmos)
endif

.PHONY: help
help:
	@echo "Usage: make [run|waves|clean|check] test=<name> [build=rtl|nmos]"
	@echo ""
	@echo "Examples:"
	@echo "  make run   test=mytest        (defaults to build=rtl)"
	@echo "  make check test=mytest build=nmos"
	@echo "  make waves test=mytest build=rtl"

# Require test=... for real goals (not help/clean) only
ifneq ($(strip $(MAKECMDGOALS)),)
  NEED_TEST := $(filter-out help clean,$(MAKECMDGOALS))
  ifneq ($(NEED_TEST),)
    ifeq ($(strip $(test)),)
      $(error Missing required variable: test. Try: make help)
    endif
  endif
endif

# ---------- your variables ----------
COMP  = $(shell which iverilog)
RUN   = $(shell which vvp)
RM    = /usr/bin/rm
TL    = /usr/bin/tail
CWD   = $(shell pwd)

# Use build selector to pick sources, grab "./mioc-*" only directories
#
V_SRC = $(shell find ../. -name "*mioc*.v" | grep "\./mioc-" | grep "_$(build)" 2>/dev/null)

# ---------- targets ----------
.PHONY: all clean run waves tester_build waves_build tester_run check
all: run

tester_build : clean $(V_SRC)
	$(COMP) -DTESTER $(V_SRC) ./tests/$(test)/testbench.v

waves_build : clean $(V_SRC)
	$(COMP) $(V_SRC) ./tests/$(test)/testbench.v

run : waves_build
	@printf "Running test %s [build=%s]\n" "$(test)" "$(build)"
	$(RM) -f ./tests/$(test)/DATA_OUT/*.*
	$(RUN) a.out
	$(TL) -n +4 ./waves.vcd > ./tests/$(test)/DATA_OUT/waves.vcd
	$(RM) -f ./waves.vcd

waves: run
	gtkwave ./tests/$(test)/DATA_OUT/waves.vcd ./tests/$(test)/waves.gtkw

tester_run : tester_build
	@printf "Running tester version of: %s [build=%s]\n" "$(test)" "$(build)"
	$(RM) -f ./tests/$(test)/DATA_OUT/*.*
	$(RUN) a.out
	$(TL) -n +4 ./waves.vcd > ./tests/$(test)/DATA_OUT/tester.vcd
	$(RM) -f ./waves.vcd

check: tester_run ./tests/$(test)/DATA_GOLD/tester.vcd ./tests/$(test)/DATA_OUT/tester.vcd
	@errors=$$(diff ./tests/$(test)/DATA_OUT/tester.vcd ./tests/$(test)/DATA_GOLD/tester.vcd | wc -l 2>/dev/null); \
	printf "\n\nCompared DATA_OUT vcd to DATA_GOLD vcd\n"; \
	printf "%s errors found.\n" "$$errors"

clean:
	$(RM) -f a.out *.xcf
