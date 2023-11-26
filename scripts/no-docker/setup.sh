#!/bin/bash
echo "Don't run this right away! This is a template to understand how to set it up."
exit

# Clone the repo and cd to it
sudo apt install python3 python3-venv npm nginx
python3 -m venv venv
source venv/bin/activate
pip3 install poetry
npm install
sudo cp files/nginx-main.conf /etc/nginx/conf.d/wizarr.conf
# Edit /etc/nginx/conf.d/wizarr.conf to have "root /path/to/wizarr/dist/apps/wizarr-frontend;"
sudo cp scripts/no-docker/wizarr.service /etc/systemd/system/wizarr.service
# Edit /etc/systemd/system/wizarr.service to have "ExecStart=/path/to/wizarr/scripts/no-docker/start.sh"
sudo systemctl daemon-reload
sudo systemctl enable --now nginx
sudo systemctl reload nginx
sudo systemctl enable --now wizarr
