#!/bin/bash

set -o errexit
set -o nounset


IFNAME=$1
LOCAL_IP=$(ip addr list ${IFNAME} | grep "^    inet " | cut -d ' ' -f 6 | cut -d '/' -f 1 | head -n 1)
VIP=$2
GATEWAY=""
EIP=""
eip_alloc_id=""
region=$(curl http://169.254.169.254/2014-11-05/meta-data/placement/availability-zone 2> /dev/null | sed s/.$//)

if [ $# -ge 3 ]; then
  GATEWAY=$3
fi

if [[ $# == 4 ]]; then
  EIP=$4
  eip_alloc_id=$(aws ec2 describe-addresses --region ${region} --filters Name=public-ip,Values=${EIP} --output text | cut -f 2)
  if [[ ${eip_alloc_id} == "" ]]; then
    echo "Could not discover allocation ID for EIP: ${EIP}, aborting...."
    exit 1
  fi
fi

# discover AWS network interfaces
# put into series of index-matched lists
instance_id=$(curl http://169.254.169.254/2014-11-05/meta-data/instance-id 2> /dev/null)
macs_raw=$(curl http://169.254.169.254/2014-11-05/meta-data/network/interfaces/macs/ 2> /dev/null)
macs=()
ifids=()
ifnames=()
for mac in ${macs_raw}; do
  mac=${mac%/}
  macs+=(${mac})
  ifids+=($(curl http://169.254.169.254/2014-11-05/meta-data/network/interfaces/macs/${mac}/interface-id 2> /dev/null))
  ifnames+=($(ip link list | grep -B1 ${mac} | head -n 1  | cut -d ':' -f 2 | cut -d ' ' -f 2))
done

if_id=""
if_mac=""
if_idx=-1
for (( i=0; i<${#macs[@]}; i++ ));
do
  if [[ ${ifnames[$i]} == ${IFNAME} ]]; then
    #echo $i ": ifname: " ${ifnames[$i]} ", mac: " ${macs[$i]} ", ifid: " ${ifids[$i]}
    if_id=${ifids[$i]}
    if_mac=${macs[$i]}
    if_idx=$i
  fi
done

if [[ ${if_idx} == -1 ]]; then
  echo "ERROR: Interface ${IFNAME} not found"
  exit 1
fi

echo "adding/moving ip ${VIP} to ${if_id} (${IFNAME}-${if_mac}) on ${instance_id}"

# actually do it
aws ec2 assign-private-ip-addresses \
  --network-interface-id ${if_id} \
  --private-ip-addresses ${VIP} \
  --allow-reassignment \
  --region ${region}

# If a gateway has been set, mostly applicable to multi-homed hosts, setup routing to the alternate gateway
if [[ "${GATEWAY}" != "" ]]; then
  if cat /etc/iproute2/rt_tables | grep '^200 out' > /dev/null
  then
    echo out table already exists
  else
    echo "200 out" >> /etc/iproute2/rt_tables
  fi

  if ip rule list | grep "lookup out" > /dev/null
  then
    echo routes already applied
  else
    echo applying routes
    ip route add default via ${GATEWAY} dev ${IFNAME} table out
    ip rule add from ${LOCAL_IP}/32 table out
    ip rule add to ${LOCAL_IP}/32 table out
    ip rule add to ${VIP}/32 table out
    ip rule add from ${VIP}/32 table out
    ip route flush cache
  fi
fi

# Run the EIP change
if [[ "${eip_alloc_id}" != "" ]]; then
  echo "adding/moving elastic ip ${EIP} (${eip_alloc_id}) as well..."
  aws ec2 associate-address --region ${region} --allocation-id ${eip_alloc_id} --network-interface-id ${if_id} --private-ip-address ${VIP}
fi

