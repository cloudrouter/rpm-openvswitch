%global _hardened_build 1

# option to build without dpdk
%bcond_without dpdk
%define dpdk_ver 16.07

%define ver 2.6.0
%define rel 2
#define snapver 13096.gitb55205dd

%define srcver %{ver}%{?snapver:-%{snapver}}

# If wants to run tests while building, specify the '--with check'
# option. For example:
# rpmbuild -bb --with check openvswitch.spec

Name: openvswitch
Version: %{ver}
Release: %{?snapver:0.%{snapver}.}%{rel}%{?dist}
Summary: Open vSwitch daemon/database/utilities

# Nearly all of openvswitch is ASL 2.0.  The bugtool is LGPLv2+, and the
# lib/sflow*.[ch] files are SISSL
# datapath/ is GPLv2 (although not built into any of the binary packages)
# python/compat is Python (although not built into any of the binary packages)
License: ASL 2.0 and LGPLv2+ and SISSL
URL: http://openvswitch.org
Source0: http://openvswitch.org/releases/%{name}-%{version}%{?snap_gitsha}.tar.gz

# snapshot creation script, not used for build itself
# Source100: ovs-snapshot.sh

ExcludeArch: ppc

BuildRequires: autoconf automake libtool
BuildRequires: systemd-units openssl openssl-devel
BuildRequires: python python-twisted-core python-zope-interface PyQt4
BuildRequires: desktop-file-utils python-six
BuildRequires: groff graphviz git

%if %{with dpdk}
BuildRequires: dpdk-devel >= %{dpdk_ver}
BuildRequires: autoconf automake
BuildRequires: numactl-devel libpcap-devel
Provides: %{name}-dpdk = %{version}-%{release}
%endif

Requires: openssl iproute module-init-tools
%{?systemd_requires}

Obsoletes: openvswitch-controller <= 0:2.1.0-1

%bcond_with check

%description
Open vSwitch provides standard network bridging functions and
support for the OpenFlow protocol for remote per-flow control of
traffic.

%package -n python-openvswitch
Summary: Open vSwitch python bindings
License: ASL 2.0
BuildArch: noarch
Requires: python

%description -n python-openvswitch
Python bindings for the Open vSwitch database

%package test
Summary: Open vSwitch testing utilities
License: ASL 2.0
BuildArch: noarch
Requires: python-openvswitch = %{version}-%{release}
Requires: python python-twisted-core python-twisted-web

%description test
Utilities that are useful to diagnose performance and connectivity
issues in Open vSwitch setup.

%package devel
Summary: Open vSwitch OpenFlow development package (library, headers)
License: ASL 2.0
Provides: openvswitch-static = %{version}-%{release}

%description devel
This provides static library, libopenswitch.a and the openvswitch header
files needed to build an external application.

%package ovn-central
Summary: Open vSwitch - Open Virtual Network support
License: ASL 2.0
Requires: openvswitch openvswitch-ovn-common

%description ovn-central
OVN, the Open Virtual Network, is a system to support virtual network
abstraction.  OVN complements the existing capabilities of OVS to add
native support for virtual network abstractions, such as virtual L2 and L3
overlays and security groups.

%package ovn-host
Summary: Open vSwitch - Open Virtual Network support
License: ASL 2.0
Requires: openvswitch openvswitch-ovn-common

%description ovn-host
OVN, the Open Virtual Network, is a system to support virtual network
abstraction.  OVN complements the existing capabilities of OVS to add
native support for virtual network abstractions, such as virtual L2 and L3
overlays and security groups.

%package ovn-vtep
Summary: Open vSwitch - Open Virtual Network support
License: ASL 2.0
Requires: openvswitch openvswitch-ovn-common

%description ovn-vtep
OVN vtep controller
%package ovn-common
Summary: Open vSwitch - Open Virtual Network support
License: ASL 2.0
Requires: openvswitch

%description ovn-common
Utilities that are use to diagnose and manage the OVN components.

%package ovn-docker
Summary: Open vSwitch - Open Virtual Network support
License: ASL 2.0
Requires: openvswitch openvswitch-ovn-common python-openvswitch

%description ovn-docker
Docker network plugins for OVN.

%prep
%autosetup -n %{name}-%{srcver}

%build
%if %{with dpdk}
unset RTE_SDK
. /etc/profile.d/dpdk-sdk-%{_arch}.sh
%endif

%if %{defined snapver}
autoreconf -i
%endif
%configure \
	--enable-ssl \
%if %{with dpdk}
	--with-dpdk=${RTE_SDK}/${RTE_TARGET} \
%endif
	--with-pkidir=%{_sharedstatedir}/openvswitch/pki \

make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch

install -p -D -m 0644 \
        rhel/usr_share_openvswitch_scripts_systemd_sysconfig.template \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/openvswitch
for service in openvswitch ovsdb-server ovs-vswitchd \
		ovn-controller ovn-controller-vtep ovn-northd; do
        install -p -D -m 0644 \
                        rhel/usr_lib_systemd_system_${service}.service \
                        $RPM_BUILD_ROOT%{_unitdir}/${service}.service
done

install -m 0755 rhel/etc_init.d_openvswitch \
        $RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/openvswitch.init

install -p -D -m 0644 rhel/etc_logrotate.d_openvswitch \
        $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/openvswitch

install -m 0644 vswitchd/vswitch.ovsschema \
        $RPM_BUILD_ROOT/%{_datadir}/openvswitch/vswitch.ovsschema

install -d -m 0755 $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifdown-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifup-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs

install -d -m 0755 $RPM_BUILD_ROOT%{python_sitelib}
mv $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/* \
   $RPM_BUILD_ROOT%{python_sitelib}
rmdir $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/

install -d -m 0755 $RPM_BUILD_ROOT/%{_sharedstatedir}/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{_includedir}/openvswitch
install -p -D -m 0644 include/openvswitch/*.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openvswitch
install -p -D -m 0644 config.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{_includedir}/openvswitch/lib
install -p -D -m 0644 lib/*.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openvswitch/lib

install -d -m 0755 $RPM_BUILD_ROOT%{_includedir}/openflow
install -p -D -m 0644 include/openflow/*.h \
        -t $RPM_BUILD_ROOT%{_includedir}/openflow

touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/conf.db
touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/system-id.conf

# remove non-packaged files from the buildroot
rm -f %{buildroot}%{_bindir}/ovs-benchmark
rm -f %{buildroot}%{_bindir}/ovs-parse-backtrace
rm -f %{buildroot}%{_bindir}/ovs-pcap
rm -f %{buildroot}%{_bindir}/ovs-tcpundump
rm -f %{buildroot}%{_sbindir}/ovs-vlan-bug-workaround
rm -f %{buildroot}%{_mandir}/man1/ovs-benchmark.1
rm -f %{buildroot}%{_mandir}/man1/ovs-pcap.1
rm -f %{buildroot}%{_mandir}/man1/ovs-tcpundump.1
rm -f %{buildroot}%{_mandir}/man8/ovs-vlan-bug-workaround.8
rm -f %{buildroot}%{_datadir}/openvswitch/scripts/ovs-save

%check
%if %{with check}
    if make check TESTSUITEFLAGS='%{_smp_mflags}' ||
       make check TESTSUITEFLAGS='--recheck'; then :;
    else
        cat tests/testsuite.log
        exit 1
    fi
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%preun
%systemd_preun openvswitch.service
%systemd_preun ovsdb-server.service
%systemd_preun ovs-vswitchd.service

%preun ovn-central
%systemd_preun ovn-northd.service

%preun ovn-host
%systemd_preun ovn-controller.service

%preun ovn-vtep
%systemd_preun ovn-controller-vtep.service

%post
%systemd_post openvswitch.service
%systemd_post ovsdb-server.service
%systemd_post ovs-vswitchd.service

%post ovn-central
%systemd_post ovn-northd.service

%post ovn-host
%systemd_post ovn-controller.service

%post ovn-vtep
%systemd_post ovn-controller-vtep.service

%postun
%systemd_postun_with_restart openvswitch.service
%systemd_postun_with_restart ovsdb-server.service
%systemd_postun_with_restart ovs-vswitchd.service

%postun ovn-central
%systemd_postun_with_restart ovn-northd.service

%postun ovn-host
%systemd_postun_with_restart ovn-controller.service

%postun ovn-vtep
%systemd_postun_with_restart ovn-controller-vtep.service

%files -n python-openvswitch
%{python_sitelib}/ovs
%doc COPYING

%files test
%{_bindir}/ovs-test
%{_bindir}/ovs-vlan-test
%{_bindir}/ovs-l3ping
%{_mandir}/man8/ovs-test.8*
%{_mandir}/man8/ovs-vlan-test.8*
%{_mandir}/man8/ovs-l3ping.8*
%{python_sitelib}/ovstest

%files devel
%{_libdir}/*.a
%{_libdir}/*.la
%{_includedir}/openvswitch/*
%{_includedir}/openflow/*
%{_includedir}/ovn/*
%{_libdir}/pkgconfig/*.pc

%files
%defattr(-,root,root)
%dir %{_sysconfdir}/openvswitch
%config %ghost %{_sysconfdir}/openvswitch/conf.db
%config %ghost %{_sysconfdir}/openvswitch/system-id.conf
%config(noreplace) %{_sysconfdir}/sysconfig/openvswitch
%config(noreplace) %{_sysconfdir}/logrotate.d/openvswitch
%{_unitdir}/openvswitch.service
%{_unitdir}/ovsdb-server.service
%{_unitdir}/ovs-vswitchd.service
%{_datadir}/openvswitch/scripts/openvswitch.init
%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
%{_datadir}/openvswitch/bugtool-plugins/
%{_datadir}/openvswitch/scripts/ovs-bugtool-*
%{_datadir}/openvswitch/scripts/ovs-check-dead-ifs
%{_datadir}/openvswitch/scripts/ovs-lib
%{_datadir}/openvswitch/scripts/ovs-vtep
%{_datadir}/openvswitch/scripts/ovs-ctl
%config %{_datadir}/openvswitch/vswitch.ovsschema
%config %{_datadir}/openvswitch/vtep.ovsschema
%{_sysconfdir}/bash_completion.d/*.bash
%{_bindir}/ovs-appctl
%{_bindir}/ovs-docker
%{_bindir}/ovs-dpctl
%{_bindir}/ovs-dpctl-top
%{_bindir}/ovs-ofctl
%{_bindir}/ovs-vsctl
%{_bindir}/ovsdb-client
%{_bindir}/ovsdb-tool
%{_bindir}/ovs-tcpdump
%{_bindir}/ovs-testcontroller
%{_bindir}/ovs-pki
%{_bindir}/vtep-ctl
%{_sbindir}/ovs-bugtool
%{_sbindir}/ovs-vswitchd
%{_sbindir}/ovsdb-server
%{_mandir}/man1/ovsdb-client.1*
%{_mandir}/man1/ovsdb-server.1*
%{_mandir}/man1/ovsdb-tool.1*
%{_mandir}/man5/ovs-vswitchd.conf.db.5*
%{_mandir}/man5/vtep.5*
%{_mandir}/man8/vtep-ctl.8*
%{_mandir}/man8/ovs-appctl.8*
%{_mandir}/man8/ovs-bugtool.8*
%{_mandir}/man8/ovs-ctl.8*
%{_mandir}/man8/ovs-dpctl.8*
%{_mandir}/man8/ovs-dpctl-top.8*
%{_mandir}/man8/ovs-ofctl.8*
%{_mandir}/man8/ovs-pki.8*
%{_mandir}/man8/ovs-vsctl.8*
%{_mandir}/man8/ovs-vswitchd.8*
%{_mandir}/man8/ovs-parse-backtrace.8*
%{_mandir}/man8/ovs-tcpdump.8*
%{_mandir}/man8/ovs-testcontroller.8*
%doc COPYING DESIGN.md INSTALL.SSL.md NOTICE README.md WHY-OVS.md
%doc FAQ.md NEWS INSTALL.DPDK.md rhel/README.RHEL
/var/lib/openvswitch
/var/log/openvswitch
%ghost %attr(755,root,root) %{_rundir}/openvswitch

%files ovn-docker
%{_bindir}/ovn-docker-overlay-driver
%{_bindir}/ovn-docker-underlay-driver

%files ovn-common
%{_bindir}/ovn-nbctl
%{_bindir}/ovn-sbctl
%{_bindir}/ovn-trace
%{_datadir}/openvswitch/scripts/ovn-ctl
%{_datadir}/openvswitch/scripts/ovn-bugtool-nbctl-show
%{_datadir}/openvswitch/scripts/ovn-bugtool-sbctl-lflow-list
%{_datadir}/openvswitch/scripts/ovn-bugtool-sbctl-show
%{_mandir}/man8/ovn-ctl.8*
%{_mandir}/man8/ovn-nbctl.8*
%{_mandir}/man8/ovn-trace.8*
%{_mandir}/man7/ovn-architecture.7*
%{_mandir}/man8/ovn-sbctl.8*
%{_mandir}/man5/ovn-nb.5*
%{_mandir}/man5/ovn-sb.5*

%files ovn-central
%{_bindir}/ovn-northd
%{_mandir}/man8/ovn-northd.8*
%config %{_datadir}/openvswitch/ovn-nb.ovsschema
%config %{_datadir}/openvswitch/ovn-sb.ovsschema
%{_unitdir}/ovn-northd.service

%files ovn-host
%{_bindir}/ovn-controller
%{_mandir}/man8/ovn-controller.8*
%{_unitdir}/ovn-controller.service

%files ovn-vtep
%{_bindir}/ovn-controller-vtep
%{_mandir}/man8/ovn-controller-vtep.8*
%{_unitdir}/ovn-controller-vtep.service

%changelog
* Sun Oct 16 2016 John Siegrist <john@complects.com> - 2.6.0-2
- Fixed incorrect source tarball URL
* Sun Oct 16 2016 John Siegrist <john@complects.com> - 2.6.0-1
- Upgrade to version 2.6.0 pulling in changes from the Fedora 24 spec for OVS
* Fri Jul 01 2016 David Jorm <david.jorm@gmail.com> - 2.5.0-1
- Upgrade to version 2.5.0 (resolves CVE-2016-2074)
* Tue Jan 12 2016 John Siegrist <john@complects.com> - 2.4.0-2
- Disabled AutoReqProv
* Wed Sep 09 2015 John Siegrist <john@complects.com> - 2.4.0-1
- Updated version to 2.4.0
* Thu Aug 06 2015 John Siegrist <john@complects.com> - 2.3.2-1
- Initial fork from Fedora project and import into CloudRouter
