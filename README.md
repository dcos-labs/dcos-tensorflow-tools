# Examples for TensorFlow on DC/OS:

## TL;DR

Run one of the examples as follows:
```bash
$ dcos package install beta-tensorflow --options=examples/EXAMPLE_NAME.json
```
(where `EXAMPLE_NAME` is the name of one the examples in the `examples` folder e.g. `mnist`)

You should then see a service named `EXAMPLE_NAME` in your DC/OS UI.

For the exact resource requirements, check the `EXAMPLE_NAME.json` file contents.

The `examples/mnist.json` example requires no GPU resources by default, 1.0 CPU, 1024 MB of memory and 1024 MB disk.

**NOTE:** Once the example has completed, the `ps-*` and `*worker-*` tasks will terminate, but the `EXAMPLE_NAME` scheduler may still remain. This can be removed (or the computation terminated) by running:
```bash
$ dcos package uninstall beta-tensorflow --app-id=/EXAMPLE_NAME
```

## The examples in detail and advanced usage

The JSON files in `examples/` are configurations for example TensorFlow jobs. Each
example specifies the number of workers, gpu workers, parameter servers, and the
necessary resources for each of those tasks. Additionally, each example provides
a job URL, a job path, and a job name. The job URL should point to either a TensorFlow
Python file or a ZIP containing a TensorFlow Python file (in addition to helper
files and potentially some data to train on). If the job URL points to a ZIP, the job
path specifies the location of the Python file with your main function within that ZIP.
The job name is simply the name of that Python file (without the `.py` extension). For
example, suppose `job_url` pointed to a ZIP with the following structure:

```
my_job
├── README.md
├── utils
    └── parse_data.py
    └── translate.py
├── data
    └── some_data1.tfrecord
    └── some_data2.tfrecord
    └── some_data3.tfrecord
├── training
    └── train_model.py
    └── eval_model.py
```

Assume that `train_model.py` contains the main function that we want to run. In
this example, we would set the job fields as follows:

```json
"job_url"  : <job_url>,
"job_path" : "my_job/training",
"job_name" : "train_model"
```

The `shared_filesystem` field is another important piece to consider in
the options file. This framework works best with a Shared Filesystem (such
as HDFS or GCS) as a backing store for summaries and checkpoint files. It
supports both HDFS and GCS, but we recommend HDFS. If your `shared_filesystem` field
is non-empty, it will be passed to your TensorFlow code at runtime as `log_dir` in the
main function. If your `shared_filesystem` field is empty, the wrapper will pass in a
persistent volume (living in `$MESOS_SANDBOX/tf-volume`) as `log_dir` instead.
Note that distributed TensorFlow will _not_ be able to recover from failures
automatically if the Chief Worker and the Parameter Servers
do not all have access to the latest checkpoint file.

### Using HDFS and TensorBoard (Recommended)

Prerequisites:

1. An installation of HDFS. This step can be easily completed with
   `dcos package install hdfs`. Make sure to wait for the installation
   to complete before continuing. You can monitor its progress with
   `dcos hdfs plan status deploy`.
1. A VPN to access your cluster's network. You can use DC/OS Tunnel
   to easily set up a VPN. Make sure to install OpenVPN (`brew install
   openvpn`), and also make sure you have SSH access to your cluster.
   Install DC/OS Tunnel with `dcos package install tunnel-cli`, then
   start the VPN with `sudo dcos tunnel vpn`. You may also need to add
   the following addresses to your DNS resolvers in your local network
   settings: 198.51.100.1, 198.51.100.2, 198.51.100.3.

To use HDFS as a Shared Filesystem, simply set the `shared_filesystem` field
to point to your HDFS installation. If you are using the default configuration
for the certified HDFS package on DC/OS, for example, set the field to:

```
hdfs://name-0-node.hdfs.autoip.dcos.thisdcos.directory:9001/path/to/folder
```

To try an example with this field already set, run `dcos package install
beta-tensorflow --options=examples/mnist-with-summaries.json`. This example
trains a simple MNIST classifier, and it writes extra summaries to TensorBoard
for visualization. This example also sets `use_tensorboard: true`, which instructs
the framework to deploy an instance of TensorBoard along with your job. Note
that this deployment of TensorBoard will only work correctly if you have
configured a Shared Filesystem.

Since you have a VPN pointed at your cluster, you can pull up
[hdfs://name-0-node.hdfs.autoip.dcos.thisdcos.directory:9001/mnistdemo](hdfs://name-0-node.hdfs.autoip.dcos.thisdcos.directory:9001/mnistdemo)
to view the TensorBoard UI. TensorBoard may take a couple of minutes to
load the summary files. Once it finishes loading, you should be able to
use this UI to visualize your model's training progress in real-time.

### Using Google Cloud Storage (Optional)

Prerequisites:

1. A GCS bucket. This bucket must either be public, or you will
   need a Service Account Key with the "Storage Admin" permission.

Although we recommend using HDFS, you can also use GCS as a Shared Filesystem. To
use GCS, set the `shared_filesystem` field to match to:

```
gs://<bucket-name>/path/to/folder
```

IMPORTANT: unless your GCS bucket is public, you will need to authenticate the framework
           with GCS. To do so, you have two options:

1. Adding a DC/OS secret called `/gcs_key` with your service account key.
1. Passing in your stringified service account key as an environment variable (WARNING: this option is significantly less secure, as your creditions will be written to an open file in `$MESOS_SANDBOX`).

To use method 1, set `use_gcs_key_secret: true` and leave `gcs_key` blank (if
this field is non-empty, it will overwrite the value pulled from your DC/OS
secret). To use method 2, set `use_gcs_key_secret: false` and paste your stringified
service account key to `gcs_key`.
