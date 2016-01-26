
This cookbook uses a variety of testing components:

- Unit tests: [ChefSpec](https://github.com/acrmp/chefspec)
- Integration tests: [Test Kitchen](https://github.com/chef/test-kitchen)
- Chef Style lints: [Foodcritic](https://github.com/acrmp/foodcritic)
- Ruby Style lints: [Rubocop](https://github.com/bbatsov/rubocop)

Prerequisites
-------------

Developing with this cookbook expects an installation of [ChefDK](https://downloads.chef.io/chef-dk/).

A bundler-based option is planned but not currently available.

You must also have Vagrant and VirtualBox installed:

- [Vagrant](https://vagrantup.com)
- [VirtualBox](https://virtualbox.org)

Once installed, you must install the `vagrant-berkshelf` plugin:

    $ vagrant plugin install vagrant-berkshelf

Running test environments
-------------------------

Once the above are installed, you should be able to run Test Kitchen:

    kitchen list
    kitchen converge centos71
    kitchen verify centos71

