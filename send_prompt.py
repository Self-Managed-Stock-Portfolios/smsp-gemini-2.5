import os
import json
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from read_portfolio import get_portfolio_string
from read_stocks import get_stock_data_string

load_dotenv()

def get_prompt_type() -> str:
    """Prompts user for prompt type and validates input.
    
    Returns:
        str: Valid prompt type ('f', 'd', or 't').
    """
    while True:
        user_input = input("Enter prompt type (f for first timer, d for daily, t for weekend training): ").strip().lower()
        if user_input in ['f', 'd', 't']:
            return user_input
        print("Invalid input. Please enter 'f', 'd', or 't'.")

def load_prompt(prompt_type: str, date_input: str) -> str:
    """Loads and processes prompt from file, substituting portfolio, stock data, and prior signals.
    
    Args:
        prompt_type (str): Type of prompt ('f', 'd', 't').
        date_input (str): Date in YYYY-MM-DD format.
    
    Returns:
        str: Processed prompt string.
    
    Raises:
        FileNotFoundError: If prompt file is missing.
        ValueError: If date format or stock data processing fails.
        json.JSONDecodeError: If prior signal JSON parsing fails.
    """
    prompt_files = {
        'f': 'first_timer_prompt.txt',
        'd': 'daily_prompt.txt',
        't': 'training_prompt.txt'
    }
    file_path = prompt_files.get(prompt_type)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file '{file_path}' not found.")
    with open(file_path, 'r', encoding='utf-8') as f:
        prompt = f.read().strip()
    
    if prompt_type in ['d', 't']:
        portfolio_str = get_portfolio_string(date_input)
        prompt = prompt.replace("[Portfolio String]", portfolio_str)
    
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
        if prompt_type == 't':
            stock_data = ""
            for i in range(5):
                past_date = (target_date - timedelta(days=i)).strftime('%Y-%m-%d')
                stock_data += get_stock_data_string(past_date) + "\n"
            prompt = prompt.replace("[Stock Data]", stock_data)
            
            prior_signals = []
            signals_dir = os.path.join("Gemini Daily Reviews", "Weekdays")
            for i in range(5):
                past_date = (target_date - timedelta(days=i)).strftime('%Y-%m-%d')
                signal_file = os.path.join(signals_dir, f"d_{past_date}.json")
                if os.path.exists(signal_file):
                    with open(signal_file, 'r', encoding='utf-8') as f:
                        signal_data = json.load(f)
                        signal_content = json.loads(signal_data['text'])
                        signal_content['date'] = past_date
                        prior_signals.append(signal_content)
            prompt = prompt.replace("[Prior Signals JSON]", json.dumps(prior_signals))
            prompt = prompt.replace("[Date]", date_input)
        else:
            stock_data = get_stock_data_string(date_input)
            prompt = prompt.replace("[Stock Data]", stock_data)
            
            if prompt_type == 'd':
                prior_signals = []
                signals_dir = os.path.join("Gemini Daily Reviews", "Weekdays")
                monday = target_date - timedelta(days=target_date.weekday())
                for i in range(target_date.weekday() + 1):
                    past_date = (monday + timedelta(days=i)).strftime('%Y-%m-%d')
                    signal_file = os.path.join(signals_dir, f"d_{past_date}.json")
                    if os.path.exists(signal_file):
                        with open(signal_file, 'r', encoding='utf-8') as f:
                            signal_data = json.load(f)
                            signal_content = json.loads(signal_data['text'])
                            signal_content['date'] = past_date
                            prior_signals.append(signal_content)
                prompt = prompt.replace("[Past Week's Signals]", json.dumps(prior_signals))
                prompt = prompt.replace("[Date]", date_input)
    
    except ValueError as e:
        raise ValueError(f"Error processing stock data: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error parsing prior signal JSON: {e}", e.doc, e.pos)
    
    return prompt

def is_weekday() -> bool:
    """Checks if today is a weekday (Monday-Friday).
    
    Returns:
        bool: True if weekday, False if weekend.
    """
    today = date.today()
    return today.weekday() < 5

def save_response(response, prompt_type: str, date_input: str):
    """Saves Gemini response as JSON to appropriate directory.
    
    Args:
        response: Gemini response object.
        prompt_type (str): Type of prompt ('f', 'd', 't').
        date_input (str): Date in YYYY-MM-DD format.
    """
    base_dir = "Gemini Daily Reviews"
    sub_dir = "Weekdays" if is_weekday() else "Weekends"
    os.makedirs(os.path.join(base_dir, sub_dir), exist_ok=True)
    
    date_str = datetime.strptime(date_input, '%Y-%m-%d').strftime('%Y-%m-%d')
    filename = f"{prompt_type}_{date_str}.json"
    filepath = os.path.join(base_dir, sub_dir, filename)
    
    response_dict = {
        "text": response.text,
        "model": "Gemini 2.5",
        "usage": {
            "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response.usage_metadata, 'prompt_token_count') else 0,
            "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response.usage_metadata, 'candidates_token_count') else 0
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(response_dict, f, indent=2)
    
    print(f"Response saved to: {filepath}")

if __name__ == "__main__":
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    
    prompt_type = get_prompt_type()
    
    date_input = input("Enter the date (YYYY-MM-DD): ").strip()
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
        if target_date.weekday() >= 5:
            print(f"Warning: {date_input} is a weekend. Consider using last trading day (e.g., 2025-09-19).")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-19).")
        exit(1)
    
    try:
        prompt = load_prompt(prompt_type, date_input)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        exit(1)
    
    temperature = 0.3 if prompt_type in ['f', 'd'] else 0.35
    
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt, generation_config={"temperature": temperature})
    
    print("Gemini Response:")
    print(response.text)
    
    save_response(response, prompt_type, date_input)