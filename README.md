# nightlife

## TODO

iterm2:
/opt/homebrew/lib/python3.11/site-packages/iterm2/
echo -e “\033]50;SetProfile=Production\a”

Dark mode notify:
git@github.com:bouk/dark-mode-notify.git
make install prefix=$HOME/.local
~/Library/LaunchAgents/ke.bou.dark-mode-notify.plist
launchctl load -w ~/Library/LaunchAgents/ke.bou.dark-mode-notify.plist

## The Pitch

Nightlife is a web service that accepts notifications on named topics with
opaque payloads. In response to each specific notification, nightlife executes
associated commands.

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

## Design

### Tools

Auth: This tool creates a public/private key-pair used to allow dispatch to send
requests to an agent. This tool is expected to be run on the local machine
through an SSH connection to the remote machine. This allows the public key to
be written to the remote machine, but the private key to be written to the local
machine.

Dispatch: This tool sends events from the Principal server to the Agent server.
Event payloads are generated by running the event's associated executable and
capture its stdout. This payload is then sent to each registered Agent.

Respond: This tool invokes topic handlers as subprocesses. Topic handlers are
discovered from the Agent server's configured topic handlers directory. The
results of invoking each handler (exit status, runtime, stdout, stderr, etc) are
collected and emitted as JSON on stdout.

Register: This tool sends a PUT request to the local Principal server to add
another machine as an agent that should be notified when certain events are
created. The Principal server is found by reading its lockfile.

Notify: This tool sends a POST request to the local Principal server to notify
it of an event. The Principal server can then respond to and broadcast the event
to registered Agent servers. The Principal server is found by reading its
lockfile.

### Servers

Agent: This server runs on the remote machine that is meant to be notified of
events on the local machine. When notifications are received, handlers are
executed using the Respond tool.

Principal: This server runs on the local machine that produces events we want to
broadcast to remote machines. We use ephemeral local configuration to find which
hosts to notify about specific events, and which keys to use to connect to their
agents. When events are created, handlers are first executed on the principal
machine using the Respond tool. Then the event is broadcast to the agent
machines using the Dispatch tool.

## Testing

```
bin/nightlife-principal --reload
bin/nightlife-agent --reload
bin/nightlife-register localagent http://127.0.0.1:8001 config/auth/keys/priv theme 0<&-
curl -H 'Accept: application/json' http://localhost:8000/agents | jq .
bin/nightlife-notify theme
```
