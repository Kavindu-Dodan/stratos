# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import paho.mqtt.publish as publish

from modules.event.instance.status.events import *
from modules.util.log import *
from modules.util import cartridgeagentutils
import healthstats
import constants
from config import Config

log = LogFactory().get_log(__name__)
publishers = {}
""" :type : dict[str, EventPublisher] """


def publish_instance_started_event():
    if not Config.started:
        log.info("Publishing instance started event...")

        application_id = Config.application_id
        service_name = Config.service_name
        cluster_id = Config.cluster_id
        member_id = Config.member_id
        instance_id = Config.instance_id
        cluster_instance_id = Config.cluster_instance_id
        network_partition_id = Config.network_partition_id
        partition_id = Config.partition_id

        instance_started_event = InstanceStartedEvent(
            application_id,
            service_name,
            cluster_id,
            cluster_instance_id,
            member_id,
            instance_id,
            network_partition_id,
            partition_id)

        publisher = get_publisher(constants.INSTANCE_STATUS_TOPIC + constants.INSTANCE_STARTED_EVENT)
        publisher.publish(instance_started_event)
        Config.started = True
        log.info("Instance started event published")
    else:
        log.warn("Instance already started")


def publish_instance_activated_event():
    if not Config.activated:
        # Wait for all ports to be active
        listen_address = Config.listen_address
        configuration_ports = Config.ports
        ports_active = cartridgeagentutils.wait_until_ports_active(
            listen_address,
            configuration_ports,
            int(Config.read_property("port.check.timeout", critical=False)))

        if ports_active:
            log.info("Publishing instance activated event...")
            service_name = Config.service_name
            cluster_id = Config.cluster_id
            member_id = Config.member_id
            instance_id = Config.instance_id
            cluster_instance_id = Config.cluster_instance_id
            network_partition_id = Config.network_partition_id
            partition_id = Config.partition_id

            instance_activated_event = InstanceActivatedEvent(
                service_name,
                cluster_id,
                cluster_instance_id,
                member_id,
                instance_id,
                network_partition_id,
                partition_id)

            publisher = get_publisher(constants.INSTANCE_STATUS_TOPIC + constants.INSTANCE_ACTIVATED_EVENT)
            publisher.publish(instance_activated_event)

            log.info("Instance activated event published")
            log.info("Starting health statistics notifier")

            health_stat_publishing_enabled = Config.read_property(constants.CEP_PUBLISHER_ENABLED, True)

            if health_stat_publishing_enabled:
                interval_default = 15  # seconds
                interval = Config.read_property("stats.notifier.interval", False)
                if interval is not None and len(interval) > 0:
                    try:
                        interval = int(interval)
                    except ValueError:
                        interval = interval_default
                else:
                    interval = interval_default
                health_stats_publisher = healthstats.HealthStatisticsPublisherManager(interval)
                log.info("Starting Health statistics publisher with interval %r" % interval)
                health_stats_publisher.start()
            else:
                log.warn("Statistics publisher is disabled")

            Config.activated = True
            log.info("Health statistics notifier started")
        else:
            log.error(
                "Ports activation timed out. Aborting publishing instance activated event [IPAddress] %s [Ports] %s"
                % (listen_address, configuration_ports))
    else:
        log.warn("Instance already activated")


def publish_maintenance_mode_event():
    if not Config.maintenance:
        log.info("Publishing instance maintenance mode event...")

        service_name = Config.service_name
        cluster_id = Config.cluster_id
        member_id = Config.member_id
        instance_id = Config.instance_id
        cluster_instance_id = Config.cluster_instance_id
        network_partition_id = Config.network_partition_id
        partition_id = Config.partition_id

        instance_maintenance_mode_event = InstanceMaintenanceModeEvent(
            service_name,
            cluster_id,
            cluster_instance_id,
            member_id,
            instance_id,
            network_partition_id,
            partition_id)

        publisher = get_publisher(constants.INSTANCE_STATUS_TOPIC + constants.INSTANCE_MAINTENANCE_MODE_EVENT)
        publisher.publish(instance_maintenance_mode_event)

        Config.maintenance = True
        log.info("Instance maintenance mode event published")
    else:
        log.warn("Instance already in a maintenance mode")


def publish_instance_ready_to_shutdown_event():
    if not Config.ready_to_shutdown:
        log.info("Publishing instance activated event...")

        service_name = Config.service_name
        cluster_id = Config.cluster_id
        member_id = Config.member_id
        instance_id = Config.instance_id
        cluster_instance_id = Config.cluster_instance_id
        network_partition_id = Config.network_partition_id
        partition_id = Config.partition_id

        instance_shutdown_event = InstanceReadyToShutdownEvent(
            service_name,
            cluster_id,
            cluster_instance_id,
            member_id,
            instance_id,
            network_partition_id,
            partition_id)

        publisher = get_publisher(constants.INSTANCE_STATUS_TOPIC + constants.INSTANCE_READY_TO_SHUTDOWN_EVENT)
        publisher.publish(instance_shutdown_event)

        Config.ready_to_shutdown = True
        log.info("Instance ReadyToShutDown event published")
    else:
        log.warn("Instance already in a ReadyToShutDown event...")


def get_publisher(topic):
    if topic not in publishers:
        publishers[topic] = EventPublisher(topic)

    return publishers[topic]


class EventPublisher:
    """
    Handles publishing events to topics to the provided message broker
    """

    def __init__(self, topic):
        self.__topic = topic

    def publish(self, event):
        mb_ip = Config.read_property(constants.MB_IP)
        mb_port = Config.read_property(constants.MB_PORT)
        mb_username = Config.read_property(constants.MB_USERNAME, False)
        mb_password = Config.read_property(constants.MB_PASSWORD, False)
        if mb_username is None:
            auth = None
        else:
            auth = {"username": mb_username, "password": mb_password}

        payload = event.to_json()
        publish.single(self.__topic,
                       payload,
                       hostname=mb_ip,
                       port=mb_port,
                       auth=auth)
