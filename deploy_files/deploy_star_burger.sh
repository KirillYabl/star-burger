#!/bin/bash
set -Eeuo pipefail

cd /opt/star-burger/
git pull origin master
echo "git ok"
npm ci
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
echo "frontend ok"
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python manage.py collectstatic --noinput
./venv/bin/python manage.py migrate --noinput
echo "backend ok"
systemctl daemon-reload
systemctl reload nginx
systemctl stop starburger-backend
systemctl start starburger-backend
echo "systemctl start ok"
last_commit_hash=$(git rev-parse HEAD)
echo $last_commit_hash
curl -H "X-Rollbar-Access-Token: PASTE_ROLLBAR_ACCESS_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "production", "revision": "'${last_commit_hash}'", "rollbar_name": "kiablunovskii", "local_username": "root", "comment": "auto deploy", "status": "succeeded"}'
echo "Деплой успешно завершен!"
