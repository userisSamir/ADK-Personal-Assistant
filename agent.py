import datetime
import requests
from zoneinfo import ZoneInfo
from google.adk.agents import Agent


from typing import Any, Dict
from google.adk.tools.tool_context import ToolContext


from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.adk.models.google_llm import Gemini
from google.genai import types
from tavily import TavilyClient

# --- v1beta add ---
from google.cloud import aiplatform
PROJECT_ID = "gen-lang-client-0580071138"
LOCATION = "us-central1"
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
    api_endpoint=f"{LOCATION}-aiplatform.googleapis.com/v1beta"
)
TAVILY_API_KEY = "your Tavily key"
OPENWEATHER_API_KEY = "your openweather key"
tavily_client = TavilyClient(api_key="your Tavily key")

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


def travel_search(query: str) -> str:
    """
    Finds real-time info about travel (flights, trains, hotels) using Tavily Search.
    """
    if not TAVILY_API_KEY or TAVILY_API_KEY == "YOUR_TAVILY_API_KEY_HERE":
        return "Error: Tavily API Key is not configured."
    try:
        response = tavily_client.search(query=query, search_depth="basic")
        
        context = "\n".join([f"Source: {obj['url']}\nContent: {obj['content']}" for obj in response['results']])
        return context
    except Exception as e:
        return f"Error during Tavily search: {e}"

def get_weather(city: str) -> dict:
    """Retrieves the CURRENT weather report for a specified city using OpenWeatherMap."""
    
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "YOUR_API_KEY_HERE":
        return { "status": "error", "error_message": "Weather API Key is not configured." }

    # OpenWeatherMap API URL
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"  
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()  # Will raise an exception for HTTP errors (e.g., 404, 500)
        
        data = response.json()
        
        if data.get("cod") != 200:
            return { "status": "error", "error_message": data.get("message", "City not found") }

        # Processing the data from the API
        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        country = data["sys"]["country"]
        
        report = (
            f"The weather in {city}, {country} is currently {weather_desc}. "
            f"The temperature is {temp}°C, but feels like {feels_like}°C. "
            f"The humidity is {humidity}%."
        )
        
        # get_current_time can use it
        timezone_offset = data.get("timezone", 0) 
        
        return { 
            "status": "success", 
            "report": report,
            "timezone_offset": timezone_offset,
            "city_name": data.get("name")
        }

    except requests.exceptions.HTTPError:
        return { "status": "error", "error_message": f"City '{city}' not found or API error." }
    except requests.exceptions.RequestException as e:
        return { "status": "error", "error_message": f"Network error: {e}" }
    except Exception as e:
        return { "status": "error", "error_message": f"An unexpected error occurred: {e}" }
    


def get_current_time(
    tool_context: ToolContext, city: str
) -> Dict[str, Any]:
    """
    Returns the current time in a specified city.
    It first tries to get timezone info from the weather tool's context (state).
    If not found, it calls the weather tool to get the timezone.
    """
    
    # ---  SPECIAL FIX FOR "INDIA" ---
    if city.lower() == "india":
        tz_offset_seconds = 19800  # IST is UTC+5:30 (19800 seconds)
        city_name = "India (IST)"
        
       
        tool_context.state["last_weather_city"] = city_name
        tool_context.state["last_weather_tz"] = tz_offset_seconds
    
    else:
        # This part runs for any other city (e.g., "New York", "Kolkata")
        
        context_city = tool_context.state.get("last_weather_city")
        context_tz_offset = tool_context.state.get("last_weather_tz")
        
        if context_city and context_city.lower() == city.lower() and context_tz_offset is not None:
            # Yes, we have the info. No need for a new API call.
            tz_offset_seconds = context_tz_offset
            city_name = context_city
        else:
            # No, we don't have the info. We need to call get_weather for the timezone.
            weather_data = get_weather(city)
            
            if weather_data["status"] == "error":
                return weather_data 

            tz_offset_seconds = weather_data["timezone_offset"]
            city_name = weather_data.get("city_name", city)
            
            # Save this info 
            tool_context.state["last_weather_city"] = city_name
            tool_context.state["last_weather_tz"] = tz_offset_seconds

    # Calculate the current time from the UTC offset
    try:
        tz = datetime.timezone(datetime.timedelta(seconds=tz_offset_seconds))
        local_time = datetime.datetime.now(tz)
        report = f'The current time in {city_name} is {local_time.strftime("%Y-%m-%d %H:%M:%S %Z")}'
        return {"status": "success", "report": report}
    except Exception as e:
        return {"status": "error", "error_message": f"Error calculating time: {e}"}
    
# save user info
def save_userinfo(
    tool_context: ToolContext, user_name: str, country: str
) -> Dict[str, Any]:
    """Tool to record and save user name and country in session state."""
    # Write to session state using the 'user:' prefix
    tool_context.state["user:name"] = user_name
    tool_context.state["user:country"] = country
    return {"status": "success"}

def retrieve_userinfo(tool_context: ToolContext) -> Dict[str, Any]:
    """Tool to retrieve user name and country from session state."""
    # Read from session state
    user_name = tool_context.state.get("user:name", "Username not found")
    country = tool_context.state.get("user:country", "Country not found")
    return {"status": "success", "user_name": user_name, "country": country}


# Create the Agent 
root_agent = Agent(
    model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
    name="Personal_Travel_Assistant", 
    
    instruction=(
        "You are a helpful and conversational AI assistant. "
        "Your primary job is to answer general questions and chat with the user. "
        
        "You ALSO have special tools. You MUST use these tools when needed:"
        "1. Use 'get_weather' for any questions about weather."
        "2. Use 'get_current_time' for any questions about the current time."
        "3. Use 'travel_search' for ANY questions about travel, flights, trains, or hotels."
        "4. Use 'save_userinfo' if the user tells you their name or country."
        "5. Use 'retrieve_userinfo' if the user asks you to remember their name."
        
        "If the user just wants to chat (e.g., 'Hello'), answer from your own knowledge."
    ),
    
    tools=[
        get_weather,
        get_current_time,
        travel_search,  
        save_userinfo,
        retrieve_userinfo
    ],
)

#  Set up Session Management 
db_url = "sqlite:///C:/Users/sb738/my_agent/multi_tool_agent/my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)

#  Create the Runner (New from Codelab) 
APP_NAME = "weather_app"
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

print("Your 'weather_time_agent' with final upgrades is ready!")
print("   - Capabilities: Weather, Time, and User Info Memory")
print(f"  - Using Memory: {session_service.__class__.__name__}")
print(f"  - Database File: {db_url}")