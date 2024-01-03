# nightlife

## TODO

split readme design between tools and servers

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

Agent: This server runs on the remote machine that is meant to be notified of
events on the local machine. When notifications are received, handlers are
executed as subprocesses of the agent server.

Dispatch: This tool posts an event notification to an agent server.

Auth: This tool creates a public/private key-pair used to allow dispatch to send
requests to an agent. This tool is expected to be run on the local machine
through an SSH connection to the remote machine. This allows the public key to
be written to the remote machine, but the private key to be written to the local
machine.

Principal: This server runs on the local machine that produces events we want to
broadcast to remote machines. We use ephemeral local configuration to find which
hosts to notify about specific events, and which keys to use to connect to their
agents.

## Testing

```
python3 principal.py --port=8000 --reload
uvicorn agent:app --port=8001 --reload
curl -X PUT \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"host":"http://localhost:8001","key_path":"config/auth/keys/priv","key_password":null,"events":["a"]}' \
    http://localhost:8000/agent/agent1
curl -H 'Accept: application/json' \
    http://localhost:8000/agents | jq .
curl -H 'Accept: application/json' \
    http://localhost:8000/agent/agent1 | jq .
curl -X POST \
    -H 'Accept: application/json' \
    -d 'dark' \
    http://localhost:8000/dispatch/a | jq .
```
