# dcos-tensorflow-tools

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
examples. The framework works best when you use GCS as a shared filesystem. To
use GCS, you will need a bucket and a Service Account with read/write access to
that bucket. Download the JSON key file for your Service Account, and add it as
a DC/OS secret with the name `gcs_key` (as described in Build Instructions). The
`shared_filesystem` field should point to this GCS bucket with the following format:

```
gs://<bucket-name>/path/to/folder
```

This path will be passed to your main function as `log_dir` at runtime. If you choose not
to specify a shared filesystem, the wrapper will pass in a persistent volume (living in
`$MESOS_SANDBOX/tf-volume`) as `log_dir` instead. Note that distributed TensorFlow will _not_
be able to recover from failures automatically if the Chief Worker and the Parameter Servers
do not all have access to the latest checkpoint file.

To create your own examples or test custom configurations, use the [bin/new-config.sh](../bin/new-config.sh)
script. It accepts the name of your example as the only argument, and it will generate a config template
in the un-tracked `examples/local/` directory.
