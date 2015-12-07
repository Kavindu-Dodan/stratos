/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

package org.apache.stratos.messaging.message.receiver.instance.notifier;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.stratos.messaging.broker.subscribe.EventSubscriber;
import org.apache.stratos.messaging.listener.EventListener;
import org.apache.stratos.messaging.util.MessagingUtil;

/**
 * A thread for receiving instance notifier information from message broker.
 */
public class InstanceNotifierEventReceiver {
    private static final Log log = LogFactory.getLog(InstanceNotifierEventReceiver.class);
    private final InstanceNotifierEventMessageDelegator messageDelegator;
    private EventSubscriber eventSubscriber;
    private boolean terminated;

    public InstanceNotifierEventReceiver() {
        InstanceNotifierEventMessageQueue messageQueue = new InstanceNotifierEventMessageQueue();
        this.messageDelegator = new InstanceNotifierEventMessageDelegator(messageQueue);
        InstanceNotifierEventMessageListener messageListener = new InstanceNotifierEventMessageListener(messageQueue);
        // Start topic subscriber thread
        eventSubscriber = new EventSubscriber(MessagingUtil.Topics.INSTANCE_NOTIFIER_TOPIC.getTopicName(),
                messageListener);
    }

    public void addEventListener(EventListener eventListener) {
        messageDelegator.addEventListener(eventListener);
    }

    public void execute() {
        synchronized (this) {
            if (terminated) {
                log.info("InstanceNotifierEventReceiver has been terminated. Event subscriber will not be created.");
                return;
            }
            try {
                Thread subscriberThread = new Thread(eventSubscriber);
                subscriberThread.start();
                if (log.isDebugEnabled()) {
                    log.debug("InstanceNotifier event message receiver thread started");
                }

                // Start instance notifier event message delegator thread
                Thread receiverThread = new Thread(messageDelegator);
                receiverThread.start();
                if (log.isDebugEnabled()) {
                    log.debug("InstanceNotifier event message delegator thread started");
                }
            } catch (Exception e) {
                if (log.isErrorEnabled()) {
                    log.error("InstanceNotifier receiver failed", e);
                }
            }
        }
        log.info("InstanceNotifierEventReceiver started");

        // Keep the thread live until terminated
        while (!terminated) {
            try {
                Thread.sleep(2000);
            } catch (InterruptedException ignore) {
            }
        }
    }

    public boolean isSubscribed() {
        return ((eventSubscriber != null) && (eventSubscriber.isSubscribed()));
    }

    public synchronized void terminate() {
        eventSubscriber.terminate();
        messageDelegator.terminate();
        terminated = true;
        log.info("InstanceNotifierEventReceiver terminated");
    }
}
