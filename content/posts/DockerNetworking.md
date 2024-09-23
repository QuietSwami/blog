+++
title = 'Quick Docker Networking Tutorial'
date = 2024-09-19T11:56:50+02:00
draft = False
+++

This tutorial focuses on two of the several networks Docker has at our disposal, Bridge and Overlay. These two networks allow for the similar uses under different cases.

In Docker, a Bridge Network is the default network. If no network is specified, Docker will assume that, when a container is deployed, it will use the default bridge network. The goal of the bridge network is to allow containers to communicate while remaining isolated from the hosts (the machine where the container are running) networks - and the outside world.

To communicate, containers connected to a bridge network can communicate using the container's name as hostname. This means that, if we deploy a container by specifying the flag `--name` or `-n`, to communicate we can use the name given to the container as the URL, instead of having to use the container's IP address in the network. Docker allows this by internally handling the DNS resolution of these names, to ensure that containers can find each other using known names and not IPs.

The isolation of the network is great and all but sometimes we need to access external networks, or at least, we might need to be able to access the application running inside of the container. For this we can open ports in the network by using the flag `-p` or `--publish`, and specifying the target port we want to open `HOST:CONTAINER`.

Having now understood how Bridge networks work, another problem arises. Bridge networks are limited to a single Docker Host (let's say, our local machine). Therefore, there is no way of connecting containers deployed in serveral machines, as we normally want to do when we use Docker Swarm.

Overlay networks solve this issue by creating a distributed network across multiple hosts (this is done using a combination of tunneling and encryption, but this is a bit hard to explain here). This creates a network where all containers attached to the network are able to communicate, even if they are running in different hosts. 

Now, due to their distributed nature, we need to find a new way to communicate. Also, with Docker Swarm, we are deploying services which can have several instances of the same application, thus complicating matters. A service in Docker is an abstraction to define how a group of containers (one or more) should run or behave. It also provides scalling, load balancing, and other things which I'll get to in another post.

So, in an Overlay Network we have two methods to communicate between containers. The first is by using the IP addresses of the container we wish to target (as we already could in a bridge network). The second is to communicate using the *service* name. Let's supose that we have two services, one called `web-server` with 3 replicas, and the other called `backend-server` with 2 replicas. For the `web-service` to communicate with the `backend-service` it can use something like `http://backend-service:<PORT>`, and the rest of the work is done by Swarm, like the load balancing between the instances of the service.

When it comes to communicating between two different bridge networks, Docker doesn’t natively support cross-network communication out of the box because bridge networks are isolated from each other. However, there are ways to enable communication between containers on different bridge networks. The key approaches involve routing traffic between the networks using either:

1. Container Networking: A container connected to both bridge networks.
2. Port Publishing and External Access: Using the host network as an intermediary.
3. Custom Network Drivers: Using more advanced configurations like macvlan drivers.

Before going through each one of the solutions, let's have a quick chat about why you would want to enable communication between containers on different networks. After all, Docker’s network model is designed with isolation in mind, providing separate namespaces for containers to enhance security, reduce interference, and ensure predictable behavior. So, why break this isolation? Here are a few scenarios where cross-network communication might be necessary:

1. **Microservices Architecture with Legacy Systems**:  
   Microservices in different networks may need to connect with legacy systems. Cross-network communication enables integration while maintaining isolation.

2. **Complex Application Segmentation**:  
   Segmenting application components into different networks improves organization. Controlled communication ensures they still function together.

3. **Enhanced Security and Compliance**:  
   Isolating sensitive services in secure networks ensures compliance. Controlled interaction allows functionality without compromising security.

4. **Multi-Host and Hybrid Deployment**:  
   Distributed applications across multiple hosts or cloud/on-prem setups may need to connect. Bridging networks enables unified communication across environments.

5. **Service Discovery Challenges**:  
   Different stages or services in isolated networks can complicate discovery. Cross-network communication ensures access to shared resources or services.

## Container Networking

Let's start with our solution by creating two separate bridge networks. We'll place one container on each network and use a third container that is attached to both networks as a communication channel, or "gateway." This container will allow the two isolated networks to communicate with each other.

### Messaging Queues

Messaging queues are communication mechanisms used to exchange data between services, applications, or componenets in a decouples and asynchrounous way. Think of it like a newsletter. You have a producer - someone who publishes the newsletter; a consumer -  the person who receives the newsletter; and a queue - similar to the mailing list, where the newsletter is stored untill all the recipients retrieve and read it. Like with a newsletter, in a messaging queue you can have several consummers which can receive and read the messages at different times. Each subscriber (consumer) consumes the content independently. Unlike traditional newsletters, you can also have several producers to the same queue. 

Also, unlike newletters, in a messaging queue system, consumers may acknoledge receipt of messages, and the queue may ensure that messages are delivered exactly once or at least once per consumer.

For this example, we'll use [RabbitMQ](https://www.rabbitmq.com), but there are several commonly used messaging queues such as [Apache Kafka](https://kafka.apache.org), [ActiveMQ](https://activemq.apache.org), [Mosquitto](https://mosquitto.org) (similar, not really a messaging queue, but a message broker), and of course solutions by your favorite hyperscaler (AWS, Azure, and the like).

### Step 0: The program

We'll deploy a program that sends and receives messages on a message queue. The idea is to deploy the same program on both networks, and send messages between the networks using the message broker. In this case, the program will do this automatically. 

```python
import pika
import time
import random
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up connection parameters
rabbitmq_host = os.getenv('RABBITMQ_HOST')  # RabbitMQ container name 

# Check if the RabbitMQ host is set
if not rabbitmq_host:
    logging.error("RABBITMQ_HOST environment variable is not set")
    exit(1)

connection_params = pika.ConnectionParameters(host=rabbitmq_host)

# Function to send messages
def send_message(channel, message):
    # Send a message back to the queue
    channel.basic_publish(exchange='',
                          routing_key='test_queue',
                          body=message)
    print(f" [x] Sent '{message}'")

# Function to handle received messages and send a response
def on_message_received(ch, method, properties, body):
    received_message = body.decode()
    print(f" [x] Received '{received_message}'")
    
    # Create a response message
    response_message = f"Response to '{received_message}' from {random.randint(1, 1000)}"
    
    # Simulate some processing time
    time.sleep(2)
    
    # Send the response message
    send_message(ch, response_message)

# Function to start the auto-messaging system
def start_auto_messaging(start_with_message):
    # Set up a connection and channel
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    

    # Declare a queue
    channel.queue_declare(queue='test_queue')

    # Check if the system should start by sending a message
    if start_with_message:
        initial_message = f"Initial message from {random.randint(1, 1000)}"
        send_message(channel, initial_message)

    # Start consuming and handle each message with the on_message_received function
    channel.basic_consume(queue='test_queue',
                          on_message_callback=on_message_received,
                          auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    # Read environment variable to check if the system should start by sending a message
    start_with_message = os.getenv('START_WITH_MESSAGE', 'false').lower() == 'true'
    
    # Start the auto-messaging system
    start_auto_messaging(start_with_message)
```

The application is simple: the application receives two environmental variable - one to check if it should start communicating, and the other with the name of the container (in this case RabbitMQ) with the messaging queue. If the application starts communicating, then it starts by sending a message with a random integer. Then, the second container will receive and send back a messgage composed of the message received and a new random integer.

NOTE: There's a slight bug in the app. You'll see that the container who sends the message is also able to read it's own message. This can be avoided by using an app ID and setting it as a property of the message 

```bash
    channel.basic_publish(exchange='',
                          routing_key='test_queue',
                          body=message,
                          properties=pika.BasicProperties(
                              app_id=app_id
                        ))
```

Then you can read the message properties, and select to only process the messages where the app_id isn't the same as the application.
I've tried to apply this, but there is some timing issues, which leads to the both containers stopping sending messages. When I don't check the app ID, the timing of the messages aligns, as the second container sends two messages in a row, which leads to the first container receiving a message and the ping-pong process of messages starts and continues correctly. If you have a solution for this problem, please don't hesitate to send me a message!

### Step 1: Setup the networks

To start, let's create the bridge networks. Remember, you can always do the same thing using Docker Compose.

```bash
docker network create bridge-net-1
docker network create bridge-net-2
```

To check if the networks were correctly created, run the following command:
```bash
docker network ls
```

The output should be something like:
```bash
code-gen ❯ docker network ls
NETWORK ID     NAME           DRIVER    SCOPE
217ae951f2e2   bridge         bridge    local
ece230c416f2   bridge-net-1   bridge    local
34d8e1e02ae2   bridge-net-2   bridge    local
d068772975fd   host           host      local
8bc70472ebe1   none           null      local
```

### Step 2: Deploy containers on each network

Next, we'll deploy the RabbitMQ container:

```bash
docker run -d --name rabbitmq --network bridge-net-1 --network bridge-net-2 rabbitmq
```

Once RabbitMQ is deployed and running, we can deploy the same container in each of the networks:

```bash
docker run -d --name app1 --network bridge-net-1 -e START_WITH_MESSAGE=true -e RABBITMQ_HOST=rabbitmq auto_messaging
docker run -d --name app2 --network bridge-net-2 -e START_WITH_MESSAGE=false -e RABBITMQ_HOST=rabbitmq auto_messaging
```

Once both containers are running, we an check on the logs that the messages are being passed correctly, even if the containers are in seperate networks. The RabbitMQ container, which is attached to both networks, is able to receive messages from both networks and passed them to the opposite network from which the message was sent.

[I've also wrote a docker-compose file to make the deployment of the application simpler](https://github.com/QuietSwami/docker-network-example/blob/main/container-networking/docker-compose.yaml).


### Overlay Networks

While overlay networks are spread across different hosts, the same process can be used. You can create two overlay networks, attach one container to both, and use that container as a communication channel between the networks. The only difference would be on network creation, where you would have to specify the overlay type.

```bash
docker network create -d overlay overlay-net-1
docker network create -d overlay overlay-net-2
```

Now, if you attempt to create these networks you might encounter the following error:

```bash
Error response from daemon: This node is not a swarm manager. Use "docker swarm init" or "docker swarm join" to connect this node to swarm and try again.
```

Overlay networks are Swarm-specific networks, and can only be created by the manager of the swarm.

To test this locally let's create a Swarm by doing `docker swarm init`, create the two networks, and lauch the application as a stack of services.
First, let's deploy RabbitMQ as a service:

```bash
docker service create --name rabbitmq --network overlay-net-1 --network overlay-net-2 --replicas 1 rabbitmq:latest
```

Notice that we aren't publishing any ports, as we are not trying to access the RabbitMQ instance from outside of both networks. Without publishing ports, only the containers connected to the network can communicate with the service. 

Now, let's deploy our services:

```bash
docker service create --name app1 --network overlay-net-1 -e START_WITH_MESSAGE=true -e RABBITMQ_HOST=rabbitmq auto_messaging
docker service create --name app2 --network overlay-net-2 -e START_WITH_MESSAGE=false -e RABBITMQ_HOST=rabbitmq auto_messaging
```

Then, we can check the logs by:

```bash
docker service logs app1
```

You should be able to see messages comming and going from the RabbitMQ between the services deployed in two different overlay networks.

## Port Publishing and External Acess

In certain cases, we might need to communicate with services running outside of your networks. For this, we need to publish ports for the containers that will communicate. In this case, we are opening these ports to the world—anyone that knows that the port is open can attempt to communicate with our services. This capability is essential for applications that need to be accessed by users or other systems outside of the Docker environment, such as web applications, APIs, or databases.

### How Port Publishing works?

When you publish a port, you map a port from the container to a port on the host machine. This allows traffic sent to the host's specified port to be routed to the corresponding port on the container. For instance, if you have a web application running in a container on port 80, you can expose it to the outside world by mapping it to a port on the host, such as port 8080.

```bash
docker service create \
  --name my-web-app \
  --publish published=8080,target=80 \
  my-web-app-image
```

While port publishing is a powerful feature, it also introduces security considerations:

1. **Open Ports**: When you expose a port, it becomes accessible to anyone who knows the host's IP address and the port number. You should take this into consideration and employ proper security measures.
2. **Secure Protocols**: Always prefer secure protocols, such as HTTPS, when exposing ports.
3. **Rate Limiting**: If you are exposing a port, be sure to implement throttling mechanisms to prevent abuse of your services.

Port publishing is a critical part of Docker use, even if you are using a Docker network. There are services that we wish to expose to be able to use them from wherever we are. If you want to know more about how to properly use Swarm, I've started a series on [Masetering Docker Swarm]({{ < ref "Mastering_Docker_Swarm_Pt._1">}}).

## Custom Network Drivers

While Bridge and Overlay networks are great out-of-the-box, there are situations where these won't suffice. For this, Docker provides a way to build *custom network drivers*, which can be customized to suit specific application requirements. This allows for greater flexibility in configuring networks.

The reasons for the use of custom drivers might differ, one use case which seems clear is when you need support for specific, non-standard, protocols (instead of HTTP, something like multicast or specifiying MTU sizes). Another case is when we need to integrate with existing entriprise networks, and better yet, with legacy systems. 

Another good reason might be the need for enhanced performace - let's say for high-performance applications, where you need to process real-time data. With a custom network driver, you can tune the network paramaters, which can lead to improvements in data transfer rates or reduced latency.

Also, by creating a custom network driver you can incorporate advanced security features, to further enhanced isolation and encryption of your data.

As you can see [here](https://github.com/veggiemonk/awesome-docker?tab=readme-ov-file#networking), there are already several network drivers developed, which could be used in you next project. These drivers add several tools on top of the default networks, from enhanced logging and monitoring capabilities to support for more complex routing policies.

The procedure to run a custom network driver is similar for all drivers. First, you install the driver on the host, then you create a network with the new driver, and you attach containers to that network. In some cases, you might need to configure the network by defining network policies for example. 

In general, custom network drivers provide the flexibility to address specific network challenges in modern applications.  


