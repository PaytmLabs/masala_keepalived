
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

# the following attributes are made to be consistent for all instances within
node.default['keepalived']['instances']['vi_1']['state'] = node['masala_keepalived']['state']
node.default['keepalived']['instances']['vi_1']['priority'] = node['masala_keepalived']['priority']
node.default['keepalived']['instances']['vi_1']['advert_int'] = node['masala_keepalived']['advert_int']
node.default['keepalived']['instances']['vi_1']['nopreempt'] = node['masala_keepalived']['nopreempt']
node.default['keepalived']['instances']['vi_1']['auth_type'] = node['masala_keepalived']['auth_type']
node.default['keepalived']['instances']['vi_1']['auth_pass'] = node['masala_keepalived']['auth_pass']
# the rest vary per instance
node.default['keepalived']['instances']['vi_1']['virtual_router_id'] = node['masala_keepalived']['vi_1']['virtual_router_id']
node.default['keepalived']['instances']['vi_1']['interface'] = node['masala_keepalived']['vi_1']['interface']
node.default['keepalived']['instances']['vi_1']['ip_addresses'] = node['masala_keepalived']['vi_1']['vip']
node.default['keepalived']['instances']['vi_1']['unicast_peer'] = [ node['masala_keepalived']['vi_1']['peer'] ]
node.default['keepalived']['instances']['vi_1']['track_script'] = node['masala_keepalived']['vi_1']['track_script']
# FIXME: wrapped cookbook does not pass this along
#node.default['keepalived']['instances']['vi_1']['unicast_src_ip'] = primary_ip

# add second instance vi_2 config if specced, same as above for vi_1
if ! node['masala_keepalived']['vi_2'].nil?
  node.default['keepalived']['instances']['vi_2']['state'] = node['masala_keepalived']['state']
  node.default['keepalived']['instances']['vi_2']['priority'] = node['masala_keepalived']['priority']
  node.default['keepalived']['instances']['vi_2']['advert_int'] = node['masala_keepalived']['advert_int']
  node.default['keepalived']['instances']['vi_2']['nopreempt'] = node['masala_keepalived']['nopreempt']
  node.default['keepalived']['instances']['vi_2']['auth_type'] = node['masala_keepalived']['auth_type']
  node.default['keepalived']['instances']['vi_2']['auth_pass'] = node['masala_keepalived']['auth_pass']
  node.default['keepalived']['instances']['vi_2']['virtual_router_id'] = node['masala_keepalived']['vi_2']['virtual_router_id']
  node.default['keepalived']['instances']['vi_2']['interface'] = node['masala_keepalived']['vi_2']['interface']
  node.default['keepalived']['instances']['vi_2']['ip_addresses'] = node['masala_keepalived']['vi_2']['vip']
  node.default['keepalived']['instances']['vi_2']['unicast_peer'] = [ node['masala_keepalived']['vi_2']['peer'] ]
  node.default['keepalived']['instances']['vi_2']['track_script'] = node['masala_keepalived']['vi_2']['track_script']

  # Also create a VRRP sync group encapsulating both interfaces
  #node.default['keepalived']['sync_groups']['vg_1']['instances'] = ['vi_1', 'vi_2']
  #node.default['keepalived']['sync_groups']['vg_1']['options'] = ['global_tracking']
  node.default['keepalived']['sync_groups'] = {
    'vg_1' => {
      'instances' => ['vi_1', 'vi_2'],
      'options' => ['global_tracking']
    }
  }
end

# add helper for aws case to config (installed below)
if node['masala_keepalived']['aws']
  node.default['keepalived']['instances']['vi_1']['notify_master'] = "/etc/keepalived/master-aws.sh #{node['masala_keepalived']['vi_1']['interface']} #{node['masala_keepalived']['vi_1']['vip']}"
  if ! node['masala_keepalived']['vi_2'].nil?
    cmd = "/etc/keepalived/master-aws.sh #{node['masala_keepalived']['vi_2']['interface']} #{node['masala_keepalived']['vi_2']['vip']}"
    # we only support eip on a secondary interface
    if node['masala_keepalived']['vi_2'].has_key?('eip')
      cmd += " #{node['masala_keepalived']['vi_2']['eip']}"
      # for the eip to work, we must also force the gateway
      cmd += " #{node['masala_keepalived']['vi_2']['gateway']}"
    end
    node.default['keepalived']['instances']['vi_2']['notify_master'] = cmd
  end
end

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

