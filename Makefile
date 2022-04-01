TREESITTER_LANGUAGES=python javascript
DEPS_GIT=$(foreach repo,$(TREESITTER_LANGUAGES),.deps/src/tree-sitter-$(repo))

.PHONY: deps
deps: $(DEPS_GIT)

# FROM: https://github.com/tree-sitter/py-tree-sitter
.deps/src/tree-sitter-%:
	@mkdir -p "$(dir $@)"
	git clone https://github.com/tree-sitter/tree-sitter-$* $@

# EOF
