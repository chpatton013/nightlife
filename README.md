# nightlife

## Design

Nightlife is a web service that accepts notifications on named topics with
opaque payloads. In response, nightlife executes commands that have been tied to
specific notifications.

## Use Case

Your local machine switches between "light" and "dark" system themes, and local
applications can detect and respond to that operating system event. But your
remote machine has no way of knowing what's happening on your local machine, so
you can't change your remote applications to respond to those events.

Enter nightlife.

The local machine notifies the remote machine about a change in the system theme
via HTTP. The remote machine is configured to execute a small set of tasks when
the notification is received that effects a theme change across all running
processes that the remote machine is interacting with.
