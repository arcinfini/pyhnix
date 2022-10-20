service = /etc/systemd/system/pyhnix.service

all: download build install

.venv:
	@echo "Creating a venv using version:"
	@python --version
	@python -m venv .venv

.PHONY: dev
dev: .venv
	@echo "Installing dependencies..."
	@. .venv/bin/activate && pip install -r requirements.txt 1> /dev/null

.PHONY: clean
clean:
	rm -rf .venv

# Moves the service file into the corresponding service directory
# Reloads and enables the service
.PHONY: install
install:
	@cp pyhnix.service $(service)
	@systemctl daemon-reload
	@systemctl enable pyhnix
	@systemctl start pyhnix
	systemctl status pyhnix

# Stops the service and removes its existence
.PHONY: uninstall
uninstall: $(service)
	@systemctl stop pyhnix
	@systemctl disable pyhnix
	@rm $(service)
	@systemctl daemon-reload

.PHONY: build
build: download
	@cd /root/pyhnix && /usr/bin/docker compose --profile build build

.PHONY: download
download:
	@cd /root/pyhnix && git pull origin main

# Makes the venv for local testing and linting
venv:
	@python -m venv ./.venv
	@. ./.venv/bin/activate && pip install -r ./requirements.txt