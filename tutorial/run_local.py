import tensorflow as tf
import hello.hello_world as job_runner

import logging

logging.basicConfig(
    format='[%(asctime)s|%(name)s|%(levelname)s]: %(message)s',
    level='INFO')
log = logging.getLogger(__name__)

server = tf.train.Server.create_local_server()
job_runner.main(server, ".", {})

log.info("Done")
