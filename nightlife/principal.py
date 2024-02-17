import base64
import logging
from collections import defaultdict

from fastapi import FastAPI, Request, HTTPException, Response
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from .dispatch import BroadcastTool, DispatchSettings, TriggerTool
from .respond import RespondTool


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s|%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class PrincipalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NIGHTLIFE_PRINCIPAL_")

    app_name: str = "Nightlife Principal"


SETTINGS = PrincipalSettings()


class Agent(BaseModel):
    name: str
    host: str
    key_path: str
    key_password: bytes | None
    events: set[str]


AGENTS: dict[str, Agent] = {}
AGENTS_BY_EVENT = defaultdict(set)


class GetAgent(BaseModel):
    name: str
    host: str
    key_path: str
    events: set[str]


class GetAgents(BaseModel):
    agents: list[GetAgent]


class PutAgent(BaseModel):
    host: str
    key_path: str
    key_password_b64: str | None
    events: set[str]


def _get_agent(agent_name: str) -> GetAgent:
    try:
        agent = AGENTS[agent_name]
    except KeyError:
        raise HTTPException(status_code=404)
    return GetAgent(
        name=agent.name,
        host=agent.host,
        key_path=agent.key_path,
        events=agent.events,
    )


app = FastAPI()


@app.middleware("http")
async def log_request(request: Request, call_next):
    logging.info(
        "client=%s:%d method=%s path=%s query=%s",
        request.client.host if request.client else "<unknown>",
        request.client.port if request.client else 0,
        request.method,
        request.url.path,
        str(request.query_params),
    )
    return await call_next(request)


@app.get("/agents")
async def get_agents() -> GetAgents:
    return GetAgents(agents=[_get_agent(name) for name in AGENTS])


@app.get("/agent/{agent_name}")
async def get_agent(agent_name: str) -> GetAgent:
    return _get_agent(agent_name)


@app.put("/agent/{agent_name}", status_code=204, response_class=Response)
async def put_agent(agent_name: str, agent: PutAgent) -> None:
    global AGENTS
    global AGENTS_BY_EVENT

    key_password: bytes | None = None
    if agent.key_password_b64:
        key_password = base64.b64decode(agent.key_password_b64)

    AGENTS[agent_name] = Agent(
        name=agent_name,
        host=agent.host,
        key_path=agent.key_path,
        key_password=key_password,
        events=agent.events,
    )

    for event_name in agent.events:
        AGENTS_BY_EVENT[event_name].add(agent_name)


@app.delete("/agent/{agent_name}", status_code=204, response_class=Response)
async def delete_agent(agent_name: str) -> None:
    global AGENTS
    global AGENTS_BY_EVENT

    agent = AGENTS[agent_name]

    for event_name in agent.events:
        AGENTS_BY_EVENT[event_name].remove(agent_name)

    del AGENTS[agent_name]


@app.post("/dispatch/{event_name}", status_code=204, response_class=Response)
async def post_dispatch(event_name: str) -> None:
    """
    Trigger the event to capture the broadcast payload. Respond to the event
    locally, then broadcast the event to all registered agents.
    """
    settings = DispatchSettings()

    try:
        body = TriggerTool(settings=settings).trigger(event_name)
    except:
        logging.exception("Failed to trigger event: %s", event_name)
        raise HTTPException(500, "trigger failed")

    try:
        RespondTool().handle_topic(event_name, body)
    except FileNotFoundError:
        # This machine might not be configured to handle this event locally, but
        # we still want to broadcast to all our registered agents.
        pass

    try:
        agent_names = AGENTS_BY_EVENT[event_name]
    except KeyError:
        # There may not be any registered agents for this event.
        return

    for agent_name in agent_names:
        try:
            agent = AGENTS[agent_name]
        except KeyError:
            raise HTTPException(500, "server misconfiguration")

        broadcast = BroadcastTool(
            agent_host=agent.host,
            private_key_file=agent.key_path,
            private_key_password=agent.key_password,
            settings=settings,
        )
        try:
            broadcast.broadcast(event_name, body)
        except:
            raise HTTPException(500, "broadcast failed")
