
# Cookbook Name:: masala_keepalived
# Recipe:: default
#
# Copyright 2016, Paytm Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

primary_if = node['network']['interfaces'][node['system']['primary_interface']]
primary_addrs = primary_if['addresses']
primary_addrs_ipv4 = primary_addrs.select { |_addr, attrs| attrs['family'] == 'inet' }
primary_ip = primary_addrs_ipv4.keys.first

# map simplified vars over
# we only use the instance_defaults, not the built-in multi-node vars
node.default['keepalived']['global']['router_id'] = node['masala_keepalived']['name']

# accumulate interfaces for sync group
sync_members = []
["vi_1", "vi_2", "vi_3"].each do |vi|
  if ! node['masala_keepalived'][vi].nil?
    # the following attributes are made to be consistent for all instances within
    node.default['keepalived']['instances'][vi]['state'] = node['masala_keepalived']['state']
    node.default['keepalived']['instances'][vi]['priority'] = node['masala_keepalived']['priority']
    node.default['keepalived']['instances'][vi]['advert_int'] = node['masala_keepalived']['advert_int']
    node.default['keepalived']['instances'][vi]['nopreempt'] = node['masala_keepalived']['nopreempt']
    node.default['keepalived']['instances'][vi]['auth_type'] = node['masala_keepalived']['auth_type']
    node.default['keepalived']['instances'][vi]['auth_pass'] = node['masala_keepalived']['auth_pass']
    # the rest vary per instance
    node.default['keepalived']['instances'][vi]['virtual_router_id'] = node['masala_keepalived'][vi]['virtual_router_id']
    node.default['keepalived']['instances'][vi]['interface'] = node['masala_keepalived'][vi]['interface']
    node.default['keepalived']['instances'][vi]['ip_addresses'] = node['masala_keepalived'][vi]['vip']
    node.default['keepalived']['instances'][vi]['unicast_peer'] = [ node['masala_keepalived'][vi]['peer'] ]
    node.default['keepalived']['instances'][vi]['track_script'] = node['masala_keepalived'][vi]['track_script']
    # add to group
    sync_members << vi
    # check for AWS support
    if node['masala_keepalived']['aws']
      cmd = "/etc/keepalived/master-aws.sh #{node['masala_keepalived'][vi]['interface']} #{node['masala_keepalived'][vi]['vip']}"
      if node['masala_keepalived'][vi].has_key?('eip') and node['masala_keepalived'][vi].has_key?('gateway')
        if vi != "vi_1"
          cmd += " #{node['masala_keepalived'][vi]['eip']}"
          # for the eip to work, we must also force the gateway
          cmd += " #{node['masala_keepalived'][vi]['gateway']}"
	else
          raise "eip not supported on primary interface"
        end
      end
      node.default['keepalived']['instances'][vi]['notify_master'] = cmd
    end
  else
    if vi == "vi_1"
      raise "vi_1 virtual interface must exist in configuration"
    end
  end
end

# Add accumulated sync members to group
node.default['keepalived']['sync_groups'] = {
  'vg_1' => {
    'instances' => sync_members,
    'options' => ['global_tracking']
  }
}

# add notify helper for aws support
if node['masala_keepalived']['aws']
  cookbook_file '/etc/keepalived/master-aws.sh' do
    source 'master-aws.sh'
    owner 'root'
    group node.root_group
    mode '0755'
    action :create
    notifies :restart, "service[keepalived]"
  end
end

include_recipe 'masala_base::default'
include_recipe 'masala_snmpd::default'
include_recipe 'keepalived::default'
include_recipe 'masala_keepalived::datadog'

