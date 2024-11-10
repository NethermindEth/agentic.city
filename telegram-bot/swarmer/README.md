Swarmer is like openai's swarm but less
less is more


Features
# Agent identity
An agent identity is specified by a UUID

Instruction
# Handoff functionality
The AI runner can subsitute the operating agent in entirity while maintaining the history of the current invokation of the chat with the agent (the message log)
Tools can specify agents which are to be handed over to.

# Parallel Tool use
Agents should be able to evoke tools in parallel

The following is an example of a response from chatgpt
```
ModelResponse(id='chatcmpl-ARrz19OS9RSi3cAYbexBQxcedCct3', created=1731205731, model='gpt-3.5-turbo-0125', object='chat.completion', system_fingerprint=None, choices=[Choices(finish_reason='tool_calls', index=0, message=Message(content=None, role='assistant', tool_calls=[ChatCompletionMessageToolCall(function=Function(arguments='{"location":"Boston","unit":"celsius"}', name='get_current_weather'), id='call_pwjncOZJA1C8Zm20sDzr3lCG', type='function')], function_call=None))], usage=Usage(completion_tokens=20, prompt_tokens=83, total_tokens=103, completion_tokens_details=CompletionTokensDetailsWrapper(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0, text_tokens=None), prompt_tokens_details=PromptTokensDetailsWrapper(audio_tokens=0, cached_tokens=0, text_tokens=None, image_tokens=None)), service_tier=None)
```

# Dynamic tools
It should be easy to change the toolset of an agent
Updating this set should be provided as a tool

# Tool Creation
Agents should be able to create their own tools

# Wakeup
Agents must be able to define a cron-like job which runs at regular intervals OR
be able to subscribe to streams of data.
Agents should be able to define code transformations over these data.
Agents should wake up from these streams.


Getting started:

Set the environment variables for your model as demonstrated here:
https://docs.litellm.ai/docs/#litellm-python-sdk
