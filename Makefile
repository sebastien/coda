DEPS_GIT:=$(foreach repo,$(TREESITTER_LANGUAGES),.deps/src/tree-sitter-$(repo))
SOURCES_PY:=$(wildcard src/py/*/*.py  src/py/*/*/*.py src/py/*/*/*/*.py)
PRODUCT_SO:=$(SOURCES_PY:src/py/%.py=.build/lib/py/%.so)
PRODUCT_ALL:=$(PRODUCT_SO)

REQUIRE_PY=pyflakes bandit mypy
PREP_ALL=$(REQUIRE_PY:%=build/require-py-%.task)

PYTHON=python
PYTEST=$(PYTHON)
SOURCES_PY=$(wildcard src/py/*/*.py src/py/*/*/*.py )
TREESITTER_LANGUAGES=python javascript

# Commands
BANDIT=python -m bandit
PYFLAKES=python -m pyflakes
MYPY=python -m mypy
MYPYC=mypyc

cmd-check=if ! $$(which $1 &> /dev/null ); then echo "ERR Could not find command $1"; exit 1; fi; $1


.PHONY: prep
prep: $(PREP_ALL)
	@

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
test: $(PREP_ALL)
	@if ! $(PYTEST) ./tests/harness.py ./tests/*.*; then
		echo "!!! ERR Tests failed"
		exit 1
	fi

.PHONY: check
check: check-bandit check-flakes check-strict

.PHONY: check-bandit
check-bandit: $(PREP_ALL)
	@$(BANDIT) -r -s B101 src/py/coda

.PHONY: check-flakes
check-flakes: $(PREP_ALL)
	@$(PYFLAKES) $(SOURCES_PY)

.PHONY: check-mypyc
check-mypyc: $(PREP_ALL)
	@$(call cmd-check,mypyc)  $(SOURCES_PY)

.PHONY: check-strict
check-strict: $(PREP_ALL)
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
deps/src/tree-sitter-%:
	@mkdir -p "$(dir $@)"
	git clone https://github.com/tree-sitter/tree-sitter-$* $@

build/require-py-%.task:
	@
	if $(PYTHON) -mpip install --user --upgrade '$*'; then
		mkdir -p "$(dir $@)"
		touch "$@"
	fi

# .build/lib/py/%.so: src/py/%.py
# 	@mkdir -p "$(notdir $@)"
# 	mypyc $@

print-%:
	$(info $*=$($*))


.ONESHELL:
# EOF
