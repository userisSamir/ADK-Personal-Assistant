Personal Travel Assistant (ADK Agent)

This project is a submission for the "Agents Intensive - Capstone Project" hackathon. It is an "all-in-one" conversational AI assistant built using the Google Agent Development Kit (ADK).


 Features Implemented

This agent successfully demonstrates **5 key concepts** from the hackathon list(5 day ai-agent course-2025):

1.  Agent powered by an LLM: Uses `gemini-2.0-flash` for reasoning and natural language conversation.
2.  Custom Tools: Features 5 custom-built Python tools that connect to real-world APIs:
     `travel_search`: Fetches real-time travel (flights, trains) info using the **Tavily API**.
     `get_weather`: Fetches live weather data from the **OpenWeatherMap API**.
     `get_current_time`: Provides the correct time for any city, handling timezones.
     `save_userinfo`: Saves user details (like name/country) to the session state.
     `retrieve_userinfo`: Retrieves saved user details from the session state.
3.  Long term memory: Uses `DatabaseSessionService` to save all conversations and state to a local `my_assistant_memory.db` file. This allows the agent's memory to persist even after restarting the server.
4.  Sessions & state management: Uses `ToolContext` (`tool_context.state`) to manage session-specific data. This is used by `get_current_time` to remember the city from a previous turn (`last_weather_city`) and by `retrieve_userinfo` to remember the user's name across the conversation.
5.  Context engineering: A detailed `instruction` prompt guides the agent on *when* to use its specific tools (like `travel_search` for travel) versus *when* to answer from its own knowledge (for general chat).

 How to Run This Project

 1. Clone the Repository
    
git clone [https://github.com/userisSamir/ADK-Personal-Assistant](https://github.com/userisSamir/ADK-Personal-Assistant)

2. Create a Stable Environment

cd ADK-Personal-Assistant

py  -m venv .venv

.\venv\Scripts\activate.bat

3. Install Dependencies
Install all required packages from the requirements.txt file:

pip install -r requirements.txt

4. Set API Keys 
This agent requires two API keys to function. You must set them as environment variables.

for Windows Command Prompt

set TAVILY_API_KEY=your_tavily_key_here

set OPENWEATHER_API_KEY=your_weather_key_here


5. Run the Agent
Once the environment is activated and keys are set, run the adk web command from the project's root directory:

adk web


The agent will be available at http://127.0.0.1:8000/  .

