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

The `shared_filesystem` field is the last important piece to consider in the
examples. This framework supports both HDFS and GCS as shared filesystems for
summaries and checkpoint files. The `shared_filesystem` field should point
to either GCS or HDFS with the following format:

```
hdfs://<hdfs-location>/path/to/folder
gs://<bucket-name>/path/to/folder
```

See "Using HDFS" or "Using Google Cloud Storage" for details regarding each option. We
recommend using HDFS along with the official HDFS package in the Service Catalog.

The shared filesystem will be passed to your main function as `log_dir` at runtime. If you choose not
to specify a shared filesystem, the wrapper will pass in a persistent volume (living in
`$MESOS_SANDBOX/tf-volume`) as `log_dir` instead. Note that distributed TensorFlow will _not_
be able to recover from failures automatically if the Chief Worker and the Parameter Servers
do not all have access to the latest checkpoint file.

To create your own examples or test custom configurations, use the [bin/new-config.sh](../bin/new-config.sh)
script. It accepts the name of your example as the only argument, and it will generate a config template
in the un-tracked `examples/local/` directory.

## Using HDFS

To use HDFS as a shared filesystem, you will need to have an HDFS installation. The easiest approach is
to install HDFS on your DC/OS Cluster using the official HDFS package. You can install it with one
click from the Service Catalog.

If you just installed HDFS on your cluster, make sure it has finished deploying before continuing. You can
verify that the deployment has completed with `dcos hdfs plan status deploy`.

Once you have HDFS installed, try running the `mnist-hdfs.json` example:

```
dcos package install beta-tensorflow --options=examples/mnist-hdfs.json
```

Note that if you did not install HDFS from the Service Catalog, or if you performed a non-standard
installation, you may need to edit `mnist-hdfs.json` to point to your HDFS cluster.

## Using Google Cloud Storage

To use GCS with DC/OS TensorFlow, there are 2 options:

1. Adding a DC/OS secret called `/gcs_key` with your service account key.
2. Passing in your stringified service account key as an environment variable (WARNING: this option is significantly less secure, as your creditions will be written to an open file in `$MESOS_SANDBOX`).

The first steps to using GCS are to create a bucket, create a service acount with the "Storage Admin" permission for that bucket, and download the service account JSON key. To use method 1, set `use_gcs_key_secret: true` and leave `gcs_key` blank (if this field is non-empty, it will overwrite the value pulled from your DC/OS secret). To use method 2, set `use_gcs_key_secret: false` and paste your stringified service account key to `gcs_key`.

## Using TensorBoard

If you are using a shared filesystem, you also have the option to deploy an instance of TensorBoard
along with your TensorFlow job. To do this, simply set `use_tensorboard: true` in your options file.

The `mnist-hdfs.json` example has this option enabled by default. So, if you followed the instructions under
"Using HDFS" to run that example, you will already have an instance of TensorBoard running with your job.

To view the TensorBoard UI, assuming you are not on the same network as your DC/OS cluster, you will need
to use a VPN. DC/OS Tunnel makes this easy. Run `dcos package install tunnel-cli --cli` to install the DC/OS
Tunnel CLI. Then, run `sudo dcos tunnel vpn` to enable the VPN.

Finally, open up (http://tensorboard.mnist-hdfs.l4lb.thisdcos.directory:6006)[http://tensorboard.mnist-hdfs.l4lb.thisdcos.directory:6006]
to view the TensorBoard UI.
