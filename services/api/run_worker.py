from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker
from worker import consumer


def main():
    print("Starting consumer...", flush=True)
    while True:
        try:
            consumer.consume()
        except (AMQPConnectionError, ConnectionClosedByBroker) as e:
            print(str(e))
            continue


if __name__ == "__main__":
    main()
