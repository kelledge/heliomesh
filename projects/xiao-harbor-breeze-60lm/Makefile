PROJECT_NAME := xiao-harbor-breeze-60lm
HELIOMESH_BUILD_DIR ?= ../../build
PROJECT_BUILD_DIR ?= $(HELIOMESH_BUILD_DIR)/$(PROJECT_NAME)

.PHONY: build
build:
	kibot -L $(PROJECT_BUILD_DIR)/kibot.log -c xiao-harbor-breeze-60lm.kibot.yaml
	find $(PROJECT_BUILD_DIR) -type f -path "*/reports/*.json" | xargs -n 1 kicad2junit --input

.PHONY: clean
clean:
	rm -rf $(PROJECT_BUILD_DIR)
