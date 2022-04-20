.PHONY: \
	build-dev \
	test-unit-dev \
	test-functional-dev \
	coverage-dev \
	lint-dev \
	run-dev \
	build-run-dev \
	down-dev \
	build-prod \
	run-prod \
	build-run-prod \
	down-prod
build-dev:
	docker-compose -f config/docker/dev/docker-compose.yml build
test-unit-dev:
	docker-compose -f config/docker/dev/docker-compose.yml run web pytest tests/unit
test-functional-dev: _up-dev _sleep
	docker-compose -f config/docker/dev/docker-compose.yml run web pytest tests/functional
	docker-compose -f config/docker/dev/docker-compose.yml down
coverage-dev: _up-dev _sleep
	docker-compose -f config/docker/dev/docker-compose.yml run web pytest \
		--cov=common --cov=web --cov=worker --cov-report term-missing tests
	docker-compose -f config/docker/dev/docker-compose.yml down
lint-dev:
	docker-compose -f config/docker/dev/docker-compose.yml run web mypy run_web.py
	docker-compose -f config/docker/dev/docker-compose.yml run web mypy run_worker.py
	docker-compose -f config/docker/dev/docker-compose.yml run web flake8 .
	docker-compose -f config/docker/dev/docker-compose.yml run web black --check .
format-dev:
	docker-compose -f config/docker/dev/docker-compose.yml run web black .
run-dev:
	docker-compose -f config/docker/dev/docker-compose.yml up
build-run-dev:
	docker-compose -f config/docker/dev/docker-compose.yml up --build
down-dev:
	docker-compose -f config/docker/dev/docker-compose.yml down --remove-orphans
build-prod:
	docker-compose -f config/docker/prod/docker-compose.yml build
run-prod:
	docker-compose -f config/docker/prod/docker-compose.yml up --scale worker=2
build-run-prod:
	docker-compose -f config/docker/prod/docker-compose.yml up --scale worker=2 --build
down-prod:
	docker-compose -f config/docker/prod/docker-compose.yml down --remove-orphans
_up-dev:
	docker-compose -f config/docker/dev/docker-compose.yml up -d
_sleep:
	sleep 10
