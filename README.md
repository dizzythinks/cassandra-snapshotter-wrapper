# cassandra-snapshotter-wrapper

A wrapper script for [cassandra-snapshotter](https://github.com/tbarbugli/cassandra_snapshotter).

Why?
====

cassandra-snapshotter is great for creating full backups of your Cassandra clusters in S3. However, it is a command line tool which takes many arguments so when running from cron it can become messy. Additionally, as it is quite noisy with its output. This was a quick hack up to:

* supress/redirect the output in a friendler way
* make it nicer to manage new backup requirement via a config file
* dynamically find my cassandra clusters that run in autoscale groups
* a stop-gap that would be quicker than forking and refactoring the original

Requirements
============

Runs in Python 2.7. Non-standard library modules required are:

PyYAML==3.10
boto==2.32.1

Assumes that you have installed cassandra-snapshotter and that you have a user set-up called cassandrasnapshotter on your clusters with relevant sudo privileges.

Additional IAM privileges to cassandra-snapshotter's S3 access are EC2-read only


Setup
=====

Take the sample snapshotter_config.yaml and add your set-up and save on the host that will run the snapshotter in /etc/snapshotter_config.yaml. Most options are self-explanatory, however note:

myproduct: this represents the -p argument when run_snapshotter.py is called as per usage below
autoscale_group: this is the long name of your autoscale group as per the EC2 console

        snapshot:
            myproduct:
                aws_access_key_id: 'XXXXXXXXXXXXXXXXXXXX'
                aws_secret_access_key: 'XXXXXXXXXXXXXXXXXXX'
                s3_bucket_name: 'mybucket'
                s3_bucket_region: 'eu-west-1'
                s3_base_path: 'mybackup'
                autoscale_group: 'myautoscalegroup'

You will now need to create /var/log/snapshotter and ensure that the user you intend to use has write access to it. Logs will appear here in the format myproduct_snapshotter.log


Usage
=====

        usage: run_snapshotter.py [-h] -p P

        Run Cassandra Snapshotter

        optional arguments:
          -h, --help  show this help message and exit
          -p P        Product as per config.yaml e.g. myproduct

