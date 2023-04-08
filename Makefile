PROJECT = terraform-ecs-redeploy
FUNCTION = $(PROJECT)

all: build

.PHONY: build clean

build: clean
	cd src; pip install -r requirements.txt -t ./
	cd src; zip -X -r $(FUNCTION).zip . -x "*__pycache__*"
	cp src/$(FUNCTION).zip build/
	rm src/$(FUNCTION).zip

clean:
	rm -rf build/*

.PHONY: install
install:
	@rbenv install -s
	@gem install overcommit && overcommit --install && overcommit --sign pre-commit
