+++
title = 'Mastering Docker Swarm Pt.1'
date = 2024-06-17T11:56:50+02:00
draft = true
+++

Docker Swarm integrates clustering seamlessly with Docker, connecting Docker Daemons into a single, unified network. In a Docker Swarm cluster, one (or more) node is designated as the master (or manager), while the rest are worker nodes. The master node is responsible for distributing services across the worker nodes and ensuring that the desired state of each service is maintained.

For this demonstration, I have created a Docker Swarm cluster on AWS, consisting of 3 master nodes and 3 worker nodes. This setup is designed to test High Availability within Docker Swarm. By having multiple master nodes, the cluster remains operational even if one master node fails, ensuring continuous service availability.

## DNS-Based Discovery and Overlay Networks

DNS-based service discovery is a fundamental feature of Docker Swarm that facilitates service-to-service communication. When you deploy a service in Docker Swarm, it automatically registers with the swarm's internal DNS server. Each service is assigned a unique DNS name, which is accessible throughout the swarm cluster.

The internal DNS server in Docker Swarm manages the resolution of service names to their corresponding IP addresses. This allows containers to resolve service names to the IP addresses of the service's tasks, enabling straightforward communication between services using DNS queries.

Docker Swarm employs round-robin load balancing by default when multiple instances (tasks) of a service are running. When a service name is queried, the DNS server returns the IP addresses of all active tasks for that service. The Docker engine then balances incoming requests among these tasks, distributing the load evenly.

Each service in a Docker Swarm can be accessed by its name. For example, if you deploy a service called `web`, other services can access it using the name `web`.

### Example

First, we are going to create an Overlay network called `my_network`. This network will allow communication between containers deployed on different machines, enabling seamless service discovery and interaction across the swarm.


```bash
docker network create --driver overlay my_network --attachable
```

Let's inspect the network to verify its creation and configuration:


```bash
docker network inspect my_network
```
```json
[
    {
        "Name": "test_network",
        "Id": "j94uo2esqbrk0uy54c0xtq4dg",
        "Created": "2024-06-17T11:44:15.377226457Z",
        "Scope": "swarm",
        "Driver": "overlay",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "10.0.1.0/24",
                    "Gateway": "10.0.1.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": null,
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "4097"
        },
        "Labels": null
    }
]
```

As you can see, there should be no peers nor any containers specified in the output. Peers are the nodes that are connected to the network, and they only connect once a service which uses the network is deployed on it. 

Next, we'll deploy the first service, ensuring that we specify the network we want the service to be attached to:

```bash
docker service create --name web --replicas 3 --network my_network nginx
```

> Node: Docker automatically assigns DNS names for services. If you want to specify a custom DNS name, you can use the `--dns-name` flag. For example, `--dns-name myweb` will allow access via `myweb`.

In this example, we've created a service named `web` composed of 3 replicas running nginx. When this service is deployed, Docker Swarm automatically assigns DNS entries for it, allowing other services within the same network to resolve web to the IP addresses of its tasks.


Now, to further test the DNS-Based Discovery, let's run a busybox service, attach it to the same network, and then test the DNS resolution from within a container. 

> Note: BusyBox is a lightweight, single executable that provides many common UNIX utilities, making it ideal for embedded systems and minimal environments. It combines tiny versions of many common commands, making it versatile and efficient for containerized environments.

```bash
docker service create --name app --replicas 3 --network my_network busybox:latest sleep 3600
```
> Note: notice the `sleep 3600`. This will keep the busybox active for 1 hour. Without this command, the busybox starts and terminates immediately.

We can now check the status of the services to confirm they are running:

```bash
docker service ls
```
Output:

```bash
ID            NAME      MODE        REPLICAS  IMAGE          PORTS
j94uo2esqbrk  web       replicated  3/3       nginx:latest   
k4t5u8w9x6y0  app       replicated  3/3       busybox:latest 
```

To test the DNS resolution, we'll access one of the busybox containers and attempt to ping the `web` service:

1. Identify a Running Container:
    First, SSH into a machine that is running the `busybox` container. You can find out which node is running the `busybox` containers by inspecting the tasks of the `app` service:

    ```bash
    docker service ps app
    ```
2. Access the container
    Once on the appropriate node, use `docker exec` to get a shell inside one of the busybox containers:
    ```bash
    docker exec -it <busybox-container-id> /bin/sh
    ```
    or:
    ```bash
    docker exec -it $(docker ps -q --filter "name=app") /bin/sh
    ```
3. Ping the `web` Service:
    Inside the container, use the `ping` command to test the DNS resolution of the web service:
    ```bash
    ping web
    ```

Output:
```bash
PING web (10.0.1.2): 56 data bytes
64 bytes from 10.0.1.2: seq=0 ttl=64 time=0.045 ms
64 bytes from 10.0.1.3: seq=1 ttl=64 time=0.040 ms
64 bytes from 10.0.1.4: seq=2 ttl=64 time=0.042 ms
```
This confirms that the `web` service is accessible by its DNS name `web`, and that the internal DNS server is correctly resolving the name to the IP addresses of the `web` service's tasks. This DNS-based service discovery allows applications running inside the overlay network to communicate with each other seamlessly.


## Ingress Load Balancing

In Docker Swarm, the ingress load balancer distributes incoming network traffic across multiple service replicas, essential for scaling services and ensuring high availability.

Docker Swarm uses an internal overlay network called the ingress network to handle incoming traffic. When a service is created with published ports, Docker Swarm automatically creates and manages the ingress network. This network spans all nodes in the swarm, enabling them to accept incoming traffic on the published ports.

The routing mesh is a critical component that routes incoming requests to any node in the Docker Swarm cluster, regardless of where the service tasks are running. The routing mesh ensures that traffic can reach the service even if its tasks are distributed across multiple nodes. This is achieved using IP Virtual Server (IPVS) for load balancing, which operates at the Linux kernel level to efficiently route traffic.

Previously, we've seen how to communicate between tasks in a swarm. Each node in the network keeps the DNS records of the overlay networks to which they belong. When a service is deployed, the internal DNS server updates all nodes with the necessary DNS records. This allows any node to resolve the service name to the appropriate virtual IP, ensuring that requests can be properly routed to available containers. The load balancing is performed in a round-robin fashion across healthy service instances.

When a node receives a request for a published port, but the target container is not on that node, the routing mesh forwards the request to a node that is running the desired service instance. Since all nodes have a replica of the DNS records for the ingress network, they can efficiently redirect the traffic to the appropriate service instance.

{{ $image := resources.Get "images/sunset.jpg" }}


### Benefits of Docker's Ingress Load Balancer
- Simplifies Traffic Management:
    - Automatically handles incoming traffic and distributes it across service instances.
    - No need for external load balancers for basic load balancing needs.
- High Availability:
    - Ensures that traffic is distributed evenly, preventing any single instance from becoming a bottleneck.
    - Supports failover by routing traffic to healthy instances if some go down.
- Scalability:
    - Easily scale services up or down, and the ingress load balancer adjusts traffic distribution accordingly.
- Flexibility:
    - Supports various deployment modes and configurations to suit different use cases.

#### Limitations
- Basic Load Balancing:
    - The built-in load balancer uses a simple round-robin algorithm, which may not be sufficient for more complex traffic management needs.
- Performance Overhead:
    - The routing mesh introduces some performance overhead due to the additional network hops.
- Limited Customization:
    - For more advanced routing and load balancing features, external tools like Traefik or NGINX might be required.



