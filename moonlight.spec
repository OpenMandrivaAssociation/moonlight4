%define major 0
%define libname %mklibname moon %major
%define develname %mklibname -d moon
%define monover 2.6.1
%define monobasicver 2.6

Summary: Open Source implementation of Silverlight
Name: moonlight
Version: 2.4.1
Release: 1
Source0: http://ftp.novell.com/pub/mono/sources/moon/%version/%name-%{version}.tar.bz2
#gw these differ from the release tarballs
Source1: http://ftp.novell.com/pub/mono/sources/moon/%version/mono-%monover.tar.bz2
Source2: http://ftp.novell.com/pub/mono/sources/moon/%version/mono-basic-%monobasicver.tar.bz2
Patch: moon-2.0-format-strings.patch
Patch1: moon-2.0-fix-linkage.patch
#gw fix building with --no-undefined enabled
Patch5: mono-2.0-fix-linking.patch
Patch8: mono-2.6-format-strings.patch
Patch9:  bad-register.patch
Patch11: moonlight-2.3-firefox-4.0.patch
Patch12: moonlight-2.4.1-use-correct-mono-lib-flags.patch
Patch13: moonlight-2.4.1-drop-dead-curl-header.patch
License: LGPLv2
Group: System/Libraries
Url: http://www.mono-project.com/Moonlight
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires: ffmpeg-devel
BuildRequires: libxtst-devel
BuildRequires: libxrandr-devel
%if %mdvver >= 201000
BuildRequires: xulrunner-devel
%else
BuildRequires: xulrunner-devel-unstable
%endif
BuildRequires: libcairo-devel >= 1.6
BuildRequires: gnome-desktop-sharp-devel
BuildRequires: chrpath
BuildRequires: libgtk+2.0-devel
BuildRequires: libmagick-devel
BuildRequires: dbus-glib-devel
BuildRequires: libalsa-devel
BuildRequires: libpulseaudio-devel
BuildRequires: mono-devel >= 2.6
%if %mdvver >= 201100
BuildRequires: ndesk-dbus-devel 
%else
BuildRequires: ndesk-dbus
%endif
BuildRequires: curl-devel
BuildRequires: bison
BuildRequires: zip
Requires: %libname >= %version
Provides: moon
Obsoletes: moon

%description
Moonlight is an open source implementation of Microsoft Silverlight
for Unix systems. It supports rich browser applications, similar to
Adobe Flash.

%package doc
Summary:	Documentation for %name
Group:		Development/Other
Requires(post): mono-tools >= 1.1.9
Requires(postun): mono-tools >= 1.1.9

%description doc
This package provides API documentation for %name.

%package -n %libname
Group:System/Libraries
Summary: Open Source implementation of Silverlight

%description -n %libname
Moonlight is an open source implementation of Microsoft Silverlight
for Unix systems. It supports rich browser applications, similar to
Adobe Flash.

%package -n %develname
Group:Development/C++
Summary: Open Source implementation of Silverlight
Requires: %libname = %version-%release
Provides: libmoon-devel = %version-%release
Provides: %name-devel = %version-%release

%description -n %develname
Moonlight is an open source implementation of Microsoft Silverlight
for Unix systems. It supports rich browser applications, similar to
Adobe Flash.


%prep
%setup -q -a 1 -a 2
%patch -p1
%patch1 -p1 -b .fix-linking~
%if %mdvver >= 201100
%patch11 -p1
%endif
%patch12 -p1 -b mono_libs~
%patch13 -p1 -b .curl~
autoreconf -fi
cd mono-%monover
%patch5 -p1 -b .linking~
%patch8 -p1 -b .format-strings~
%patch9
cd ../mono-basic-%monobasicver/vbnc/vbnc
#gw rename source file with parenthesis
sed -i -e "s^(^^" -e "s^)^^" vbnc.exe.sources
for x in source/Parser/Parser\(*.vb;do
  mv "$x" $(echo "$x" | sed -e "s^(^^" -e "s^)^^")
done


%build
TOP=`pwd`
cd mono-%{monover}
./configure --prefix=${TOP}/install \
            --with-mcs-docs=no \
            --with-ikvm-native=no

make EXTERNAL_MCS=false EXTERNAL_RUNTIME=false
make install
cd ..
# libtool is evil, if the .la is present things get jacked up
find install -name \*.la -delete
# Configure against the junk install of mono
export PATH=${TOP}/install/bin:${PATH}
export LD_LIBRARY_PATH=${TOP}/install/lib:${LD_LIBRARY_PATH}
export PKG_CONFIG_PATH=${TOP}/install/lib/pkgconfig:${PKG_CONFIG_PATH}
# And then we build moonlight
%configure2_5x --without-testing --without-performance --without-examples \
  --disable-debug --disable-sanity \
  --with-ff3=yes \
  --with-cairo=system \
  --with-mcspath=${TOP}/mono-%{monover}/mcs --with-mono-basic-path=${TOP}/mono-basic-%{monobasicver} \
  --with-curl=system \
  --enable-desktop-support --enable-sdk
# We need the system gac for gtk-sharp
# Only if we're linking to the junk mono
export MONO_GAC_PREFIX=${TOP}/install:%{_prefix}
#gw parallel build does not work in 2.0
make

%install
rm -rf %{buildroot}

%makeinstall_std 
mkdir -p %buildroot%_libdir/mozilla/plugins
export PATH=%{_builddir}/%name-%version/install/bin:${PATH}
export LD_LIBRARY_PATH=%{_builddir}/%name-%version/install/lib:${LD_LIBRARY_PATH}
export PKG_CONFIG_PATH=%{_builddir}/%name-%version/install/lib/pkgconfig:${PKG_CONFIG_PATH}
%{__make} install DESTDIR=%{buildroot}
# Copy the custom libmono.so.0 for the plugin to use
install -m 644 %{_builddir}/%name-%version/install/lib/libmono.so.0 %{buildroot}%{_libdir}/moonlight/
# Make the loader pull in the correct libmono
chrpath -r  %{_libdir}/moonlight %{buildroot}%{_libdir}/moonlight/plugin/libmoon*.so
ln -s %_libdir/moonlight/plugin/libmoonloader.so %buildroot%_libdir/mozilla/plugins
rm -f %buildroot%_libdir/moon/plugin/README

%clean
rm -rf %{buildroot}

%post doc
%_bindir/monodoc --make-index > /dev/null

%postun doc
if [ "$1" = "0" -a -x %_bindir/monodoc ]; then %_bindir/monodoc --make-index > /dev/null
fi

%files
%defattr(-,root,root)
%doc README TODO
%_bindir/mopen
%_bindir/mxap
%_bindir/respack
%_bindir/smcs
%_bindir/sockpol
%_bindir/unrespack
%_bindir/xaml2html
%_bindir/xamlg
%_prefix/lib/mono/gac/Moon*
%_prefix/lib/mono/gac/System.Windows.Browser/
%_prefix/lib/mono/gac/System.Windows.Controls/
%_prefix/lib/mono/gac/System.Windows.Controls.Data/
%_prefix/lib/mono/gac/System.Windows
%_libdir/mozilla/plugins/libmoon*
%dir %_prefix/lib/mono/%name
%_prefix/lib/mono/%name/*.dll
%dir %_prefix/lib/%name
%dir %_prefix/lib/%name/2.0-redist
%_prefix/lib/%name/2.0-redist/*
%dir %_prefix/lib/%name/2.0
%_prefix/lib/%name/2.0/*
%dir %_libdir/%name
%_libdir/%name/mopen.exe*
%_libdir/%name/mxap.exe*
%_libdir/%name/respack.exe*
%_libdir/%name/sockpol.exe*
%_libdir/%name/xaml2html.exe*
%_libdir/%name/xamlg.exe*
%dir %_libdir/%name/plugin
%_libdir/%name/plugin/*.*
%_mandir/man1/mopen.1*
%_mandir/man1/mxap.1*
%_mandir/man1/respack.1*
%_mandir/man1/sockpol.1*
%_mandir/man1/svg2xaml.1*
%_mandir/man1/xamlg.1*

%files -n %libname
%defattr(-,root,root)
%_libdir/libmoon.so.%{major}*
%{_libdir}/moonlight/libmono.so.%{major}*

%files -n %develname
%defattr(-,root,root)
%_bindir/munxap
%_libdir/%name/munxap.exe*
%_libdir/libmoon.so
%_libdir/*.la
%_datadir/pkgconfig/%{name}*.pc

%files doc
%defattr(-,root,root)
%_prefix/lib/monodoc/sources/%name-gtk*
