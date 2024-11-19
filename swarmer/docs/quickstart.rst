Quick Start Guide
===============

Basic Usage
----------

Here's a simple example of creating an agent with a custom context:

.. code-block:: python

   from swarmer.agent import Agent
   from swarmer.contexts.base import BaseContext

   # Create a custom context
   class GreetingContext(BaseContext):
       def process_message(self, message: str) -> str:
           return f"Hello! You said: {message}"

   # Create an agent
   agent = Agent("my_agent")

   # Attach the context
   agent.attach_context(GreetingContext())

   # Process a message
   response = agent.process_message("Hi there!")
   print(response)  # Output: "Hello! You said: Hi there!"

Using Multiple Contexts
--------------------

Contexts can be combined to create more complex behaviors:

.. code-block:: python

   class TimeContext(BaseContext):
       def process_message(self, message: str) -> str:
           return f"[{datetime.now()}] {message}"

   class UppercaseContext(BaseContext):
       def process_message(self, message: str) -> str:
           return message.upper()

   agent = Agent("multi_context_agent")
   agent.attach_context(TimeContext())
   agent.attach_context(UppercaseContext())

   response = agent.process_message("hello")
   # Output: "[2024-02-20 10:30:15] HELLO"

Creating Custom Tools
------------------

Tools can be created to extend agent capabilities:

.. code-block:: python

   from swarmer.tools.utils import tool

   @tool
   def calculate_sum(agent_identity: str, numbers: str) -> str:
       """Calculate the sum of comma-separated numbers.

       Args:
           agent_identity: The agent using the tool
           numbers: Comma-separated list of numbers

       Returns:
           The calculated sum as a string
       """
       nums = [float(n.strip()) for n in numbers.split(",")]
       return f"The sum is: {sum(nums)}"
