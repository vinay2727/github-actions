import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import RecordType, ARecord

# Azure credentials and configuration
RESOURCE_GROUP_NAME = os.getenv("AZURE_RESOURCE_GROUP_NAME")  # Resource group containing the Private DNS Zone
DNS_ZONE_NAME = os.getenv("AZURE_PRIVATE_DNS_ZONE_NAME")  # The private DNS zone (e.g., "myprivatezone.local")

# Initialize Azure clients
credential = DefaultAzureCredential()
subscription_client = SubscriptionClient(credential)
dns_client = DnsManagementClient(credential, subscription_id=None)  # subscription_id is None since it's dynamic

def update_dns_for_containers():
    # Fetch all subscriptions in the tenant
    subscriptions = subscription_client.subscriptions.list()

    # Iterate over all subscriptions
    for subscription in subscriptions:
        subscription_id = subscription.subscription_id
        print(f"Processing subscription: {subscription.display_name} ({subscription_id})")
        
        # Initialize the ACI client for this subscription
        aci_client = ContainerInstanceManagementClient(credential, subscription_id)

        # Fetch all container groups (ACI instances) in all resource groups of this subscription
        container_groups = aci_client.container_groups.list()

        for container_group in container_groups:
            if container_group.ip_address and container_group.ip_address.ip:
                ip_address = container_group.ip_address.ip
                container_name = container_group.name
                
                print(f"Updating DNS for container '{container_name}' with IP '{ip_address}'")
                
                # Create or update A record in Private DNS Zone
                dns_client.record_sets.create_or_update(
                    RESOURCE_GROUP_NAME,
                    DNS_ZONE_NAME,
                    container_name,  # Record name (same as container name)
                    RecordType.A,
                    {
                        "ttl": 300,  # Time to live (in seconds)
                        "arecords": [ARecord(ipv4_address=ip_address)]
                    }
                )

if __name__ == "__main__":
    update_dns_for_containers()
