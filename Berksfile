source "https://supermarket.chef.io"

cookbook 'keepalived', :git => 'https://github.com/PaytmLabs/chef-keepalived.git', :ref => 'feature-instance-attrs-fix'

# Due to a design decision in berkshelf to not recursively resolve dependencies, we must declare all dependencies of our dependencies, to the full depth of the recursion

# Dependencies of masala_ldap:
cookbook 'openldap', :git => 'https://github.com/PaytmLabs/chef-openldap.git', :ref => 'feature-our-fixes'
cookbook 'masala_ldap', :git => 'https://github.com/PaytmLabs/masala_ldap.git', :ref => 'develop'

# Dependencies of masala_base:
cookbook 'ixgbevf', :git => 'https://github.com/PaytmLabs/chef-ixgbevf.git', :ref => 'master'
cookbook 'system', :git => 'https://github.com/PaytmLabs/chef-system.git', :ref => 'feature-network-restart-control'
cookbook 'masala_base', :git => 'https://github.com/PaytmLabs/masala_base.git', :ref => 'develop'

# Now load the primary metadata
metadata

