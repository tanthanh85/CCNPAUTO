# Lab 18: NetBox-Driven Loopback Automation

[Begin Lab 18](Lab18.md)

This lab installs NetBox locally and uses it as the source of truth for IOS XE loopback interfaces. A NetBox event rule triggers GitLab CI/CD after an IP address is assigned, and the protected runner deploys and verifies the intended loopbacks.
