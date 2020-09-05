import faust

from simple_settings import settings
from logging.config import dictConfig

app = faust.App(
    version=1,
    autodiscover=True,
    origin='tide_test',
    id="1",
    broker=settings.KAFKA_BOOTSTRAP_SERVER,
    logging_config=dictConfig(settings.LOGGING),
    topic_partitions=1
)


def main() -> None:
    app.main()

