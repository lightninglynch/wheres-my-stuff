# Used by `sam build`. Copies only Lambda code so .venv and detector models
# are not stuffed into the deployment zip.
.PHONY: build-IngestFunction build-AlexaSkillFunction

build-IngestFunction:
	mkdir -p "$(ARTIFACTS_DIR)"
	cp aws_backend/function.py aws_backend/__init__.py "$(ARTIFACTS_DIR)/"
	cp -R shared "$(ARTIFACTS_DIR)/"

build-AlexaSkillFunction:
	mkdir -p "$(ARTIFACTS_DIR)"
	cp alexa_skill/skill_handler.py alexa_skill/__init__.py "$(ARTIFACTS_DIR)/"
	cp -R shared "$(ARTIFACTS_DIR)/"
