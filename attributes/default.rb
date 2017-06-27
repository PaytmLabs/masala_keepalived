
# our variables for simplified use
# common/global values
default['masala_keepalived']['name'] = 'a_router'
default['masala_keepalived']['state'] = 'MASTER'
default['masala_keepalived']['priority'] = 101
default['masala_keepalived']['advert_int'] = 1
default['masala_keepalived']['nopreempt'] = false
default['masala_keepalived']['auth_type'] = 'PASS'
default['masala_keepalived']['auth_pass'] = 'abc123'
default['masala_keepalived']['aws'] = false
# attrs that will vary per instance on the node
default['masala_keepalived']['vi_1']['virtual_router_id'] = 10
default['masala_keepalived']['vi_1']['vip'] = nil        # ip to float between nodes, must be set
default['masala_keepalived']['vi_1']['track_script'] = 'chk_init'
default['masala_keepalived']['vi_1']['peer'] = nil
default['masala_keepalived']['vi_1']['interface'] = node['system']['primary_interface'] || 'eth0'

# no secondary by default, same structure as above
default['masala_keepalived']['vi_2'] = nil

# defaults we set in the wrapped cookbook
# the default check script
default['keepalived']['check_scripts']['chk_init']['script'] = 'killall -0 init'
default['keepalived']['check_scripts']['chk_init']['interval'] = 2
default['keepalived']['check_scripts']['chk_init']['weight'] = 2

# defaults for enabling snmpd integration for keepalived
default['keepalived']['env_options'] = "-D -x"
default['snmp']['additional_oids'] = ['.1.3.6.1.4.1.9586.100.5']
default['snmp']['enable_agentx'] = true


