TREESITTER_LANGUAGES=python javascript
DEPS_GIT:=$(foreach repo,$(TREESITTER_LANGUAGES),.deps/src/tree-sitter-$(repo))
SOURCES_PYTHON:=$(wildcard src/py/*/*.py  src/py/*/*/*.py src/py/*/*/*/*.py)
PRODUCT_PYTHON_SO:=$(SOURCES_PYTHON:src/py/%.py=.build/lib/py/%.so)
PRODUCT_ALL:=$(PRODUCT_PYTHON_SO)

MYPY=mypy
MYPYC=mypyc

# all: $(PRODUCT_ALL)
# 	echo $^

.PHONY: deps
deps: $(DEPS_GIT)

# FROM: https://github.com/tree-sitter/py-tree-sitter
.deps/src/tree-sitter-%:
	@mkdir -p "$(dir $@)"
	git clone https://github.com/tree-sitter/tree-sitter-$* $@

# .build/lib/py/%.so: src/py/%.py
# 	@mkdir -p "$(notdir $@)"
# 	mypyc $@

check-strict:
	@
	count_ok=0
	count_err=0
	files_err=
	for item in $(SOURCES_PYTHON); do
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

.ONESHELL:
# EOF
