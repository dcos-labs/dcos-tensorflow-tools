# Tutorial for training custom models with the DC/OS TensorFlow packages

This tutorial shows how to train custom models with the DC/OS TensorFlow package.
Please note, the outlined workflow is for the beta version of the package and will most likely change/improve with future releases.

## Prepare the Model File

We will start from the minimal [distributed TensorFlow example](https://www.tensorflow.org/deploy/distributed) below.

```python
import tensorflow as tf
c = tf.constant("Hello, distributed TensorFlow!")
server = tf.train.Server.create_local_server()
sess = tf.Session(server.target)  # Create a session on the server.
res = sess.run(c)
print (res)
```
As the DC/OS TensorFlow package is responsible for creating the server description, it wraps the actual model code and expects the following signature:

```python
def main(server, log_dir, context):
```

Where, the `server` is a tf.train.Server object which knows about every other member of the cluster.
The `log_dir` is a string providing the recommended location for training logs, summaries, and checkpoints.
And `context` is an optional dictionary of parameters (batch_size, learning_rate, etc.) specified at run-time.

After adapting the original model description, we end up with the [following model](./hello/hello_world.py).

```python
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
```

We easily test the final model locally, by using the [run_local.py](./run_local.py) script. Please make sure to [install TensorFlow](https://www.tensorflow.org/install/) beforehand.

```bash
$ python run_local.py
2017-11-26 17:00:06.076234: I tensorflow/core/distributed_runtime/rpc/grpc_channel.cc:215] Initialize GrpcChannelCache for job local -> {0 -> localhost:51224}
2017-11-26 17:00:06.076526: I tensorflow/core/distributed_runtime/rpc/grpc_server_lib.cc:324] Started server with target: grpc://localhost:51224
2017-11-26 17:00:06.080764: I tensorflow/core/distributed_runtime/master_session.cc:1004] Start master session e3b62dd340db772c with config:
b'Hello, distributed TensorFlow!'
[2017-11-26 17:00:06,108|__main__|INFO]: Done
```

In order to make this file available to our cluster, we create an archive of the hello folder and upload it to a location from where it available to the cluster. For example, in our example to [https://downloads.mesosphere.com/tensorflow-dcos/examples/hello.zip](https://downloads.mesosphere.com/tensorflow-dcos/examples/hello.zip).

## Prepare the Options File

With the current deployment model for the beta DC/OS TensorFlow package, you have to specify the model you want to run as options during the package installation (as mentioned earlier, this behavior will change in future releases).
The easiest way of specifying these options is by installing the package using the [DC/OS CLI](https://docs.mesosphere.com/latest/cli/install/).

```bash
$ dcos package install beta-tensorflow --options=OPTIONS.json
```

We provide a [script](../scripts/new-config.sh) which helps you generate a template for such option files.

```bash
$ scripts/new-config.sh helloworld
```

This command will generate the following template here `examples/local/helloworld..json`

```json
{
  "service": {
    "name": "helloworld",
    "job_url": "{{JOB_URL}}",
    "job_path": "",
    "job_name": "{{JOB_NAME}}",
    "job_context": "",
    "shared_filesystem": "",
    "use_gcs_key_secret": false,
    "use_tensorboard": false,
    "user": "root",
    "tf_image": "mesosphere/dcos-tensorflow:v1.3",
    "gpu_tf_image": "mesosphere/dcos-tensorflow:v1.3-gpu"
  },
  "gpu_worker": {
    "count": 0,
    "gpus": 1,
    "cpus": 1,
    "mem": 4096,
    "disk": 4096,
    "disk_type": "ROOT"
  },
  "worker": {
    "count": 1,
    "port": 2222,
    "cpus": 1,
    "mem": 4096,
    "disk": 4096,
    "disk_type": "ROOT"
  },
  "parameter_server": {
    "count": 1,
    "port": 2223,
    "cpus": 1,
    "mem": 4096,
    "disk": 4096,
    "disk_type": "ROOT"
  },
  "tensorboard": {
    "port": 6006,
    "cpus": 1,
    "mem": 4096
  }
}
```
All what is left for us to specify are the following variables:

* "job_url": This is the URI from where the previously created archive can be downloaded, in our case: ```"job_url": "https://downloads.mesosphere.com/tensorflow-dcos/examples/hello.zip",```
* "job_path": This is the folder within the the archive, in our case: ```"job_path": "hello",```
* "job_name": This is the name for the python file, in our case ```"job_name": "hello_world",```

The final options file can also be found [here](./helloworld.json).

```bash
$ dcos package install beta-tensorflow --options=./helloworld.json
```
Congratulations, you have just trained your first custom TensorFlow Model!

**NOTE:** Once the example has completed, the `ps-*` and `*worker-*` tasks will terminate, but the `EXAMPLE_NAME` scheduler may still remain. This can be removed (or the computation terminated) by running:
```bash
$ dcos package uninstall beta-tensorflow --app-id=/EXAMPLE_NAME
```


## Utilizing Context and Logging

To understand how to utilize context and logging let us look at the [mnist example](../examples/python/mnist.py).

```python
from tensorflow.examples.tutorials.mnist import input_data

def main(server, log_dir, context):

    # Parse context
    learning_rate = context.get('learning_rate') or 0.5
    num_training_steps = context.get('num_training_steps') or 1000000

    # Import data
    data_dir = log_dir + '/data'
    mnist = input_data.read_data_sets(data_dir, one_hot=True)
    ...
```

This `context` enables any runtime settings to be made available in main function as in this example the 'learning_rate' and 'num_training_steps'. Hence, there no need to hardcode such settings into the model (and hence no need to create/upload new models when these values change). In the [mnist.json options file](../examples/mnist.json) we set these settings as follows:

```json
    "job_context": "{\"learning_rate\":0.5,\"num_training_steps\":1000000}",
```

Furthermore, the example uses the `log_dir` as storage target when importing the input data.
