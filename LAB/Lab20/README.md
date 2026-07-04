# Lab 20: Host a CPU Monitoring Application on IOS XE

This folder contains a small Python application and a guided lab for running it inside the IOS XE Guest Shell application-hosting environment. Begin with [Lab20.md](Lab20.md).

The monitor executes a read-only IOS XE CPU command once per minute and appends UTC timestamped measurements to `bootflash:/guest-share/lab20/cpu_usage.csv`.

