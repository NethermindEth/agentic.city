from swarmer.types import AgentBase, AgentIdentity, AgentRegistry

# Global agent registry to track all active agents
# Initialized empty and populated at runtime

class AgentRegistry_(AgentRegistry):
   def __init__(self) -> None:
      self.registry: dict[str, AgentBase] = {}
      pass
   
   def get_agent(self, agent_identity: AgentIdentity) -> AgentBase:
      return self.registry[agent_identity.uuid]
   
agent_registry = AgentRegistry_()
