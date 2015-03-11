#!/usr/bin/env python
import subprocess
import sys
import logging
import yaml
import argparse
import boto.ec2
import boto.ec2.autoscale

DEBUG = False
LOG_PATH = '/var/log/snapshotter/'


def parse_args():
    parser = argparse.ArgumentParser(description='Run Cassandra Snapshotter')
    parser.add_argument('-p', action='store', required=True, help='Product as per config.yaml e.g. myproduct')
    return parser.parse_args()

args  = parse_args()

logger = logging.getLogger()
hdlr = logging.FileHandler('%s/%s_snapshotter.log' %(LOG_PATH, args.p))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


try:
    config = open('/etc/snapshotter_config.yaml')
    config = yaml.load(config)
except:
    logger.error('Could not load /etc/snapshotter_config.yaml')
    sys.exit(2)


def get_hosts_from_asg(c):
    auth_kwargs = {
               'aws_access_key_id': c['aws_access_key_id'],
               'aws_secret_access_key': c['aws_secret_access_key']
                }

    conn = boto.ec2.autoscale.connect_to_region('eu-west-1', **auth_kwargs)
    logger.info('Connecting to Autoscaling API')
    asg = c['autoscale_group']
    group = conn.get_all_groups(names=[asg])[0]
    if not group:
        logger.error('Could not find Autoscaling Group: %s' % asg)
    instances = [x.instance_id for x in group.instances]
    if not instances:
        logger.error('No instances found in %s' % asg)
        sys.exit(2)
    else:
        logger.info('Found %s instances in autoscale group %s' % (len(instances), asg))
    e_conn = boto.ec2.connect_to_region('eu-west-1', **auth_kwargs)
    logger.info('Connecting to EC2 API')
    instances = [x.public_dns_name for x in e_conn.get_only_instances(instances)]
    if not instances:
        logger.error('Unable to find instances in EC2 API')
        sys.exit(2)
    else:
        instances = ','.join(instances)
        logger.info('Found instance for autoscale group: %s' % instances)
    return instances


def get_command(c, instances):
    snapshotter = '/usr/local/bin/cassandra-snapshotter'
    command = "%s --aws-access-key-id=%s --aws-secret-access-key=%s --s3-bucket-name=%s --s3-ssenc --s3-bucket-region=%s --s3-base-path=%s backup --new-snapshot --hosts=%s --user=cassandrasnapshotter" % (
        snapshotter,
        c['aws_access_key_id'], 
        c['aws_secret_access_key'],
        c['s3_bucket_name'], 
        c['s3_bucket_region'], 
        c['s3_base_path'], 
        instances)
    return command


def main():
    logger.info('Starting Snapshotter for product %s' % args.p)
    try:
        product = config['snapshot'][args.p]
    except:
        logger.error('Product %s not found in config.yaml' % args.p)
        sys.exit(2)
    instances = get_hosts_from_asg(config['snapshot'][args.p])
    command = get_command(config['snapshot'][args.p], instances)
    if DEBUG:
        logger.debug('Executing command in subprocess: %s' % command)
    else:
        logger.info('Executing cassandra-snapshotter in subprocess')
    child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = child.stdout.readline()
        if not line:
            break
        logging.info(line)
    logging.info('Snapshotter completed')

if __name__ == "__main__":
    main()
