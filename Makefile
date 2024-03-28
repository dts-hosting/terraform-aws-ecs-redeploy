PROJECT = terraform-aws-ecs-redeploy
FUNCTION = $(PROJECT)

all: build

.PHONY: build clean debug

build: clean
	@pip install -r requirements.txt -t ./src/
	@cd src; zip -X -r $(FUNCTION).zip . -x "*__pycache__*"
	@cp src/$(FUNCTION).zip build/
	@rm src/$(FUNCTION).zip

clean:
	@rm -rf build/*

debug:
	@sam build
	@sam local invoke RedeployFunction --event events/event.json

.PHONY: install
install:
	@rbenv install -s
	@gem install overcommit && overcommit --install && overcommit --sign pre-commit
