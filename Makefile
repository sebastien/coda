TREESITTER_LANGUAGES=python javascript
DEPS_GIT:=$(foreach repo,$(TREESITTER_LANGUAGES),.deps/src/tree-sitter-$(repo))
SOURCES_PY:=$(wildcard src/py/*/*.py  src/py/*/*/*.py src/py/*/*/*/*.py)
PRODUCT_SO:=$(SOURCES_PY:src/py/%.py=.build/lib/py/%.so)
PRODUCT_ALL:=$(PRODUCT_SO)

PYTHON=python
PYTEST=$(PYTHON)
SOURCES_PY=$(wildcard src/py/*/*.py src/py/*/*/*.py )
cmd-check=if ! $$(which $1 &> /dev/null ); then echo "ERR Could not find command $1"; exit 1; fi; $1

MYPY=mypy
MYPYC=mypyc

.PHONY: run
run:
	python -m http.server

.PHONY: deps
deps: $(DEPS_GIT)
	@

.PHONY: ci
ci: check test
	@


install:
	@ln -sfr bin/code ~/.local/bin/coda

uninstall:
	@if [ -e "~/.local/bin/coda" ]; then
		unlink ~/.local/bin/coda
	fi

.PHONY: test
test:
	@if ! $(PYTEST) ./tests/harness.py ./tests/*.*; then
		echo "!!! ERR Tests failed"
		exit 1
	fi

.PHONY: check
check: check-bandit check-flakes check-strict

.PHONY: check-bandit
check-bandit:
	@$(call cmd-check,bandit) -r -s B101 src/py/coda

.PHONY: check-flakes
check-flakes:
	@$(call cmd-check,pyflakes) $(SOURCES_PY)

.PHONY: check-mypyc
check-mypyc:
	@$(call cmd-check,mypyc)  $(SOURCES_PY)

.PHONY: check-strict
check-strict:
	@
	count_ok=0
	count_err=0
	files_err=
	for item in $(SOURCES_PY); do
		if $(MYPY) --strict $$item; then
			count_ok=$$(($$count_ok+1))
		else
			count_err=$$(($$count_err+1))
			files_err+=" $$item"
		fi
	done
	summary="OK $$count_ok ERR $$count_err TOTAL $$(($$count_err + $$count_ok))"
	if [ "$$count_err" != "0" ]; then
		for item in $$files_err; do
			echo "ERR $$item"
		done
		echo "EOS FAIL $$summary"
		exit 1
	else
		echo "EOS OK $$summary"
	fi



# FROM: https://github.com/tree-sitter/py-tree-sitter
.deps/src/tree-sitter-%:
	@mkdir -p "$(dir $@)"
	git clone https://github.com/tree-sitter/tree-sitter-$* $@

# .build/lib/py/%.so: src/py/%.py
# 	@mkdir -p "$(notdir $@)"
# 	mypyc $@



.ONESHELL:
# EOF
