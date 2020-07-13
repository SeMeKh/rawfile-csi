#!/usr/bin/env python3
import logging
from concurrent import futures

import click
import grpc

import rawfile_servicer
from consts import CONFIG
from csi import csi_pb2_grpc
from metrics import expose_metrics
import rawfile_util


@click.group()
@click.option("--image-repository", envvar="IMAGE_REPOSITORY")
@click.option("--image-tag", envvar="IMAGE_TAG")
def cli(image_repository, image_tag):
    CONFIG["image_repository"] = image_repository
    CONFIG["image_tag"] = image_tag


@cli.command()
@click.option("--endpoint", envvar="CSI_ENDPOINT", default="0.0.0.0:5000")
@click.option("--nodeid", envvar="NODE_ID")
@click.option("--enable-metrics/--disable-metrics", default=True)
def csi_driver(endpoint, nodeid, enable_metrics):
    rawfile_util.migrate_all()
    if enable_metrics:
        expose_metrics()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    csi_pb2_grpc.add_IdentityServicer_to_server(
        rawfile_servicer.RawFileIdentityServicer(), server
    )
    csi_pb2_grpc.add_NodeServicer_to_server(
        rawfile_servicer.RawFileNodeServicer(node_name=nodeid), server
    )
    csi_pb2_grpc.add_ControllerServicer_to_server(
        rawfile_servicer.RawFileControllerServicer(), server
    )
    server.add_insecure_port(endpoint)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    cli()
