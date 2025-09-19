# ---------- CLI args & defaults ----------
.DEFAULT_GOAL := help

.ONESHELL:
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# rtl | nmos
build ?= rtl
IVL_FLAGS ?= -g2012             # extra iverilog flags (append via 'IVL_FLAGS+=...')

# allow only rtl or nmos
ifneq ($(filter $(build),rtl nmos),$(build))
  $(error Invalid build="$(build)". Must be rtl, or nmos)
endif

# ---------- tools ----------
COMP := $(shell command -v iverilog)
RUN  := $(shell command -v vvp)
RM   := rm
TL   := tail
GTKW := $(shell command -v gtkwave || echo gtkwave)

# ---------- help ----------
.PHONY: help
help:
	@echo "Usage: make [run|waves|clean|check|print_vars|display_vars|show_filelist] test=<name> [build=rtl|nmos]"
	@echo ""
	@echo "Overview: compiles using a per-test file list:"
	@echo "  tests/\$$test/verilog_rtl.lst   or   tests/\$$test/verilog_nmos.lst"
	@echo "Each list should contain absolute paths and/or iverilog flags (valid -f syntax)."
	@echo ""
	@echo "Examples:"
	@echo "  make run   test=mytest                  (defaults to build=rtl)"
	@echo "  make run   test=mytest build=nmos       (uses verilog_nmos.lst)"
	@echo "  make waves test=mytest                  (opens GTKWave)"
	@echo "  make show_filelist test=mytest          (prints the file list used)"
	@echo "  make display_vars                       (prints vars and exits 0)"

# Require test=... for real goals (not help/clean/print_vars/display_vars/show_filelist)
ifneq ($(strip $(MAKECMDGOALS)),)
  NEED_TEST := $(filter-out help clean print_vars display_vars show_filelist,$(MAKECMDGOALS))
  ifneq ($(NEED_TEST),)
    ifeq ($(strip $(test)),)
      $(error Missing required variable: test. Try: make help)
    endif
  endif
endif

# ---------- paths & filelists ----------
# expected to live in tests/$(test)/
FILELIST := verilog_$(build).lst
TB       := testbench.v

# ---------- utility targets ----------
.PHONY: print_vars display_vars show_filelist guard_filelist guard_tb
print_vars:
	@echo "build         = $(build)"
	@echo "test          = $(test)"
	@echo "COMP          = $(COMP)"
	@echo "RUN           = $(RUN)"
	@echo "GTKW          = $(GTKW)"
	@echo "IVL_FLAGS     = $(IVL_FLAGS)"
	@echo "FILELIST name = $(FILELIST)"
	@echo "TB            = $(TB)"
	@echo "Working dir   = $$(pwd)"

display_vars:
	@$(MAKE) -s print_vars
	@echo "=== DONE ==="
	@exit 0

show_filelist:
	@cd ./tests/$(test)
	@echo "Using: $$(pwd)/$(FILELIST)"
	@if [ ! -f "$(FILELIST)" ]; then echo "ERROR: missing $(FILELIST) in tests/$(test)"; exit 2; fi
	@echo "-----------------------------"
	@nl -ba "$(FILELIST)"
	@echo "-----------------------------"

guard_filelist:
	@cd ./tests/$(test) ; \
	if [ ! -f "$(FILELIST)" ]; then \
	  echo "ERROR: Missing $(FILELIST). Create tests/$(test)/$(FILELIST) with absolute paths or iverilog -f entries."; exit 2; \
	fi

guard_tb:
	@cd ./tests/$(test) ; \
	if [ ! -f "$(TB)" ]; then \
	  echo "ERROR: Missing $(TB) in tests/$(test)"; exit 2; \
	fi

# ---------- main targets ----------
.PHONY: all clean run waves tester_build waves_build tester_run check
all: run

# Normal (waves) build uses the selected filelist and the local testbench.v
waves_build: guard_filelist guard_tb
	cd ./tests/$(test)
	$(COMP) $(IVL_FLAGS) -o a.out -f "$(FILELIST)" "$(TB)"

# Tester build passes -DTESTER to the same filelist
tester_build: guard_filelist guard_tb
	cd ./tests/$(test)
	$(COMP) $(IVL_FLAGS) -DTESTER -o a.out -f "$(FILELIST)" "$(TB)"

run: waves_build
	printf "Running test %s [build=%s]\n" "$(test)" "$(build)"
	cd ./tests/$(test)
	mkdir -p DATA_OUT
	$(RM) -f DATA_OUT/*.* 2>/dev/null || true
	$(RUN) ./a.out
	# Remove date and time stamps, so that gold compare is agnostic
	$(TL) -n +4 waves.vcd > DATA_OUT/waves.vcd
	$(RM) waves.vcd

waves: run
	cd ./tests/$(test)
	$(GTKW) DATA_OUT/waves.vcd waves.gtkw >/dev/null 2>&1 || $(GTKW) DATA_OUT/waves.vcd

tester_run: tester_build
	printf "Running tester version of: %s [build=%s]\n" "$(test)" "$(build)"
	cd ./tests/$(test)
	mkdir -p DATA_OUT
	$(RM) -f DATA_OUT/*.* 2>/dev/null || true
	$(RUN) ./a.out
	# Remove date and time stamps, so that gold compare is agnostic
	$(TL) -n +4 waves.vcd > DATA_OUT/tester.vcd
	$(RM) waves.vcd

# Compare tester output to gold
check: tester_run
	cd ./tests/$(test)
	if [ ! -f DATA_GOLD/tester.vcd ]; then \
	  echo "ERROR: Missing DATA_GOLD/tester.vcd"; exit 2; \
	fi
	errors=$$(diff -u DATA_OUT/tester.vcd DATA_GOLD/tester.vcd | wc -l 2>/dev/null)
	printf "\n\nCompared DATA_OUT tester.vcd to DATA_GOLD tester.vcd\n"
	printf "%s errors found.\n" "$$errors"

clean:
	$(RM) -f a.out *.xcf || true
	find ./tests -maxdepth 2 -name a.out -type f -delete 2>/dev/null || true
