# Nate Backend Challenge

I just want to start by saying I enjoyed this challenge! Most interview pipelines rely heavily on timed pressure challenges which I don't think are a great test of a developer's skill, so it is refreshing to do a takeaway task. I spent a fair amount of the bank holiday weekend building it and probably went further than I should have, but I was sat in the countryside sun and enjoyed the project, so no harm done!


## Reproducibility

Everything is managed through the `Makefile`, so I suggest opening that your first stop. Here's a
summary of the commands available:
- `make build-dev` : builds development environment that hoists the `services/api` directory into the working directory (`/app`) of the container. This allows you to edit in your favourite editor while testing in a reproducible env.
- `make test-unit-dev` : runs unit tests in development environment
- `make test-functional-dev`: runs end-to-end tests in development environment
- `make coverage-dev` : runs unit & e2e tests in development environment and produces a coverage report
- `make lint-dev` : runs `mypy`, `flake8` & `black --check` in development environment and scolds you for breaking their rules
- `make format-dev` : runs black on the mounted codebase, ruthlessly reformating according to its draconian rules. I don't like all of blacks formatting choices, but I do like having it there to prevent junior devs from having schoolyard "my dad's way of formatting brackets is better than your dad's" arguments...
- `make run-dev` : stands up the whole development stack in a daemonless way so you can see the logs. From here you can usage test the api using `httpie` or your preferred tool.
- `make build-run-dev` : simply `build-dev` + `run-dev`
- `make down-dev` : tears down the development stack and cleans up
- `make build-prod` : builds "production" environment. Images are similar to the dev image, specialised to container type (e.g. web api vs worker). I've used inverted commas around "production" here to emphasise that this is obviously *not* a production stack and would require a fair bit more work to make it so.
- `make run-prod` : stands up the whole production stack in a daemonless way so you can see the logs. From here you can usage test the api using `httpie` or your preferred tool. Its more performant under load than the development stack due to `nginx` + `gunicorn` magic, but could be improved further with more work. You'll notice that I'm spinning up two consumers. This is just to emphasise how easy it is to scale this kind of arch horizontally.
- `make build-run-prod`: simply `build-prod` + `run-prod`
- `make down-prod` : tears down the production stack and cleans up

## Tech Stack and Rationale

- **Python 3.10.4** : There would be little sense in using a version of python earlier than the latest stable version as we have no backward compatability concerns.
- **Flask** : The task specification didn't explicitly require data storage, an ORM, caching or much in the way of front end rendering, so flask was the obvious choice given it's minimalist and lightweight design.
- **RabbitMQ** : Needed a message broker for my distributed design and it upports a variety of pub/sub scenarios and has decent python bindings.
- **MongoDB** : Needed a lightweight db for async job state manipulation and had no need for relational features. Plus I love its simplicity and malleability.
- **Gunicorn** : A standard go to in python apps for wsgi and works nicely with nginx
- **Nginx** : Another standard go to, in this case for load balancing
- **Docker** : The task spec required it and you rarely see any cloud deployment without it these days. Also my preferred way for managing pesky python dependencies whilst developing
- **Docker Compose** : Useful for simulating / staging microservices architectures and can easily be converted into kubernetes or open shift configs
- **Makefile** : A comfort blanket for managing cli scripts.

## A Note on Distributed System Design

I opted for a standard web-queue-worker design. Ngnix is used as a load balancer to forward requests on to a web api tier powered by gunicorn and flask. The web tier publishes word-count jobs on to a rabbitmq task queue and stores the initial job state in a mongodb database. A worker tier then consumes jobs from the queue, updating the db job state as it completes or fails the job. Users can POST jobs to the api and make GET request to check the status of their job. This design permits both vertical and horizontal scaling of web & worker tiers. Obviously, in a production scenario I would make the data and queue tiers more robust using heartbeats, sharding and add a security layer to prevent bad actors from misbehaving.

In terms of load testing, I ran `wrk` and was a little disappointed by the performance, only
managing 100 requests per second... there's probably an issue with my configuration, but its also
probably suboptimal thread context switching - multiple containers (nginx + web + worker * 2 +
rabbit + mongo) and multiple gunicorn workers.

The heftiest bodies of text I could find for testing were on project gutenberg... here's a few for
you to play with:
- https://www.gutenberg.org/files/2600/2600-h/2600-h.htm
- https://www.gutenberg.org/files/42525/42525-h/42525-h.htm
- https://www.gutenberg.org/files/1404/1404-h/1404-h.htm
- https://www.gutenberg.org/cache/epub/17439/pg17439.html

## A Note on Commenting
As a general rule, I actively try not to comment code and instead refactor it to be readable /
understandable. So you won't find many if any comments in this codebase.

## API Documentation
Lightweight documentation has been provided in  `API.md`.

## Even better if....

Thought I'd finish this ramble with a few things I wish I could improve but don't have the time to:
- **Silently Failing Endpoints**: you may notice some of the consumer tests with suspicious strings
  in their names like 'silently_fails'. This is effectively a TODO to provide better error handling
  . In general, `consumer.py` is probably my least favourite bit of code... It could do with a
  rethink.
- **Optimisation**: as mentioned before I would have liked to invest more time in configuring and
  optimising the "production" env.
- **Common Module** : the tests for the common module are a bit shallow, in fact the overall design
  of those classes could be better.
