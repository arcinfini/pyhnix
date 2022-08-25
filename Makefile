service = /etc/systemd/system/pyhnix.service

all: download build install


# Moves the service file into the corresponding service directory
# Reloads and enables the service
install:
	@mv pyhnix.service $(service)
	@systemctl daemon-reload
	@systemctl enable pyhnix
	@systemctl start pyhnix
	systemctl status pyhnix

# Stops the service and removes its existence
uninstall: $(service)
	@systemctl stop pyhnix
	@systemctl disable pyhnix
	@rm $(service)
	@systemctl daemon-reload

build: download
<<<<<<< HEAD
	@cd /root/pyhnix && /usr/bin/docker compose --profile build build
=======
	@cd /root/pyhnix && /usr/bin/docker compose --profiles build build
>>>>>>> faabad88b2027d987e11dfe2fea51c9c95393d7b

download:
	@cd /root/pyhnix && git pull origin main