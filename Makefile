makefile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
make_dir := $(dir ${makefile_path})

port?=8000
env_file?=./env
topics_dir?=./topics
lock_file?=./agent.lock
tag?=latest
extra_opts?=
args?=

build-agent:
	cd ${make_dir} && docker build \
		--file=./agent.Dockerfile \
		--tag=nightlife-agent:$(shell date --utc +%Y%M%dT%H%m%s) \
		--tag=nightlife-agent:${tag} \
		${extra_opts} \
		.

run-agent:
	cd ${make_dir} && docker run \
		--env NIGHTLIFE_AGENT_APP_NAME \
		--env NIGHTLIFE_AGENT_TOPIC_HANDLER_TIMEOUT \
		--env NIGHTLIFE_AGENT_TOPIC_HANDLER_OUTPUT_LIMIT \
		--env-file ${env_file} \
		--init \
		--interactive \
		--name=nightlife-agent-$(shell date --utc +%Y%M%dT%H%m%s) \
		--publish 8000:80 \
		--restart=on-failure \
		--tmpfs /var/run/ \
		--tty \
		--mount type=bind,src=.,dst=/opt/nightlife-agent/src/,readonly \
		--mount type=bind,src=${env_file},dst=/opt/nightlife-agent/etc/env,readonly \
		--mount type=bind,src=${topics_dir},dst=/opt/nightlife-agent/etc/topics/,readonly \
		${extra_opts} \
		nightlife-agent:${tag} \
		${args}
