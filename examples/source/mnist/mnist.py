""" demo.py

This script implements MNIST using distributed TensorFlow.

The main function is designed to be called by a wrapper. It will be
the responsibility of the wrapper to create the server, suggest a log_dir,
and pass any relevant context.
"""

import tensorflow as tf

from tensorflow.examples.tutorials.mnist import input_data


def main(server, log_dir, context):
    """
    server: a tf.train.Server object (which knows about every other member of the cluster)
    log_dir: a string providing the recommended location for training logs, summaries, and checkpoints
    context: an optional dictionary of parameters (batch_size, learning_rate, etc.) specified at run-time
    """

    # Parse context
    learning_rate = context.get('learning_rate') or 0.5
    num_training_steps = context.get('num_training_steps') or 1000000

    # Import data
    data_dir = './MNIST_DATA'
    mnist = input_data.read_data_sets(data_dir, one_hot=True)

    with tf.device(tf.train.replica_device_setter(
                    worker_device="/job:worker/task:%d" %
                    server.server_def.task_index,
                    cluster=server.server_def.cluster)):

        # Create the model
        x = tf.placeholder(tf.float32, [None, 784])
        W = tf.Variable(tf.zeros([784, 10]))
        b = tf.Variable(tf.zeros([10]))
        y = tf.matmul(x, W) + b
        y_ = tf.placeholder(tf.float32, [None, 10])
        cross_entropy = tf.reduce_mean(
            tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y))
        global_step = tf.contrib.framework.get_or_create_global_step()
        train_op = tf.train.GradientDescentOptimizer(learning_rate).minimize(
            cross_entropy, global_step=global_step)
        hooks = [tf.train.StopAtStepHook(last_step=num_training_steps)]

        # Evaluate the model
        correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

        # Add summaries
        tf.summary.scalar('accuracy', accuracy)
        merged = tf.summary.merge_all()

    # Begin distributed training
    is_chief = server.server_def.task_index == 0
    train_writer = tf.summary.FileWriter(log_dir + '/train', tf.get_default_graph()) if is_chief else None
    test_writer = tf.summary.FileWriter(log_dir + '/test') if is_chief else None
    with tf.train.MonitoredTrainingSession(master=server.target,
                                           is_chief=is_chief,
                                           hooks=hooks) as mon_sess:
        local_step = 0
        while not mon_sess.should_stop():
            if local_step % 10 == 0:
                eval_xs, eval_ys = mnist.test.images, mnist.test.labels
                summary, acc = mon_sess.run([merged, accuracy], feed_dict={x: eval_xs, y_: eval_ys})
                print('Accuracy at global step {} (local step {}): {}'.format(
                      mon_sess.run(global_step), local_step, acc))
                if is_chief:
                    test_writer.add_summary(summary, local_step)
            train_xs, train_ys = mnist.train.next_batch(100)
            summary, _ = mon_sess.run([merged, train_op], feed_dict={x: train_xs, y_: train_ys})
            if is_chief:
                train_writer.add_summary(summary, local_step)
            local_step += 1
        if is_chief:
            train_writer.close()
            test_writer.close()
