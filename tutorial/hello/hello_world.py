""" hello_world.py
"""
import tensorflow as tf

def main(server, log_dir, context):
    """
    server: a tf.train.Server object (which knows about every other member of the cluster)
    log_dir: a string providing the recommended location for training logs, summaries, and checkpoints
    context: an optional dictionary of parameters (batch_size, learning_rate, etc.) specified at run-time
    """

    c = tf.constant("Hello, distributed TensorFlow!")
    sess = tf.Session(server.target)  # Create a session on the server.
    res = sess.run(c)
    print(res) 
