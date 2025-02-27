import anthropic
import textwrap
import random
from datetime import datetime
import requests
import subprocess
import os
import json
import re  # For regex-based number conversion

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key="ANTHROPIC API KEY"  # Replace with your Anthropic API key
)

# Serp API configuration
SERP_API_KEY = "SERP API KEY"  # Replace with your Serp API key
SERP_API_URL = "https://serpapi.com/search"

# Eleven Labs API configuration
ELEVEN_LABS_API_KEY = "ELEVEN LABS API KEY"

def fetch_research_data(topic):
    """
    Fetch research data using the Serp API.
    """
    params = {
        "q": topic,
        "api_key": SERP_API_KEY,
        "num": 5  # Number of results to fetch
    }
    response = requests.get(SERP_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get("organic_results", [])
    else:
        print(f"Error fetching research data: {response.status_code}")
        return []

def list_voices(api_key):
    """
    Fetch available voices from Eleven Labs API.
    """
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        voices = response.json()["voices"]
        # Create a dictionary mapping voice names to voice IDs
        voice_map = {voice['name']: voice['voice_id'] for voice in voices}
        return voice_map
    else:
        print(f"Failed to fetch voices: {response.status_code}")
        print(response.text)
        return {}

def get_user_input(voice_map):
    podcast_name = input("Enter podcast name: ")
    topic = input("Enter podcast topic: ")
    num_speakers = int(input("Number of speakers (1-3): "))
    length = input("Podcast length (short/medium/long): ").lower()
    
    default_names = ["Alex Smith", "Jordan Taylor", "Morgan Riley", "Casey Brown", "Taylor White", "Jamie Carter", "Drew Mitchell"]
    default_genders = ["Male", "Female"]
    default_titles = ["Journalist", "Analyst", "Professor", "Researcher", "Author"]
    default_personalities = {
        "Expert": "Precise and fact-driven, citing research and breaking down complex topics with confidence.",
        "Storyteller": "Expressive and immersive, captivating audiences with vivid anecdotes.",
        "Debater": "Analytical and provocative, challenging viewpoints to spark discussion.",
        "Comedian": "Witty and sarcastic, entertaining with humor and sharp observations.",
        "Skeptic": "Thoughtful and questioning, seeking evidence before accepting claims.",
        "Enthusiast": "Passionate and energetic, diving deep into niche interests with excitement."
    }
    
    customize_speakers = input("Would you like to choose the name, gender, title, and personality for the speakers? (yes/no): ").strip().lower()
    
    speakers = []
    for i in range(num_speakers):
        if customize_speakers == "yes":
            print(f"\nEnter details for Speaker {i+1} (Press Enter to auto-generate):")
            name = input("Name: ") or random.choice(default_names)
            gender = input("Gender: ") or random.choice(default_genders)
            title = input("Title: ") or random.choice(default_titles)
            personality = input("Personality (Expert/Storyteller/Debater/Comedian/Skeptic/Enthusiast): ") or random.choice(list(default_personalities.keys()))
        else:
            name = random.choice(default_names)
            gender = random.choice(default_genders)
            title = random.choice(default_titles)
            personality = random.choice(list(default_personalities.keys()))
        
        # Assign a voice to the speaker
        print("\nAvailable Voices:")
        for j, voice_name in enumerate(voice_map.keys(), start=1):
            print(f"{j}. {voice_name}")
        voice_choice = int(input(f"Select a voice for {name} (1-{len(voice_map)}): ")) - 1
        voice_id = list(voice_map.values())[voice_choice]
        
        speakers.append({
            "name": name,
            "gender": gender,
            "title": title,
            "personality": personality,
            "description": default_personalities[personality],
            "voice_id": voice_id
        })
    
    return {
        "podcast_name": podcast_name,
        "topic": topic,
        "num_speakers": num_speakers,
        "length": length,
        "speakers": speakers
    }

def determine_length_details(length):
    """
    Define podcast length details based on user input.
    """
    length_config = {
        "short": {"duration": 5, "rebuttals": 1},  # 5 minutes, 1 round
        "medium": {"duration": 10, "rebuttals": 5},  # 10 minutes, 5 rounds
        "long": {"duration": 20, "rebuttals": 8}  # 20 minutes, 8 rounds
    }
    return length_config[length]

def convert_numbers_to_words(text):
    """
    Convert numbers and symbols in the text to their spoken equivalents.
    """
    # Replace years with their correct pronunciation
    def replace_year(match):
        year = match.group(0)
        if len(year) == 4 and year.isdigit():
            if year.startswith('20'):
                return f"two thousand and {num_to_words(year[2:])}"
            elif year.startswith('19'):
                return f"nineteen {num_to_words(year[2:])}"
        return num_to_words(year)

    # Replace numbers with words
    def replace_number(match):
        number = match.group(0)
        try:
            # Split into integer and decimal parts
            if "." in number:
                integer_part, decimal_part = number.split(".")
                return f"{num_to_words(integer_part)} point {num_to_words(decimal_part)}"
            else:
                return num_to_words(number)
        except:
            return number

    # Replace symbols with words
    text = re.sub(r'\b\d{4}\b', replace_year, text)  # Handle years
    text = re.sub(r'\d+\.\d+|\d+', replace_number, text)  # Handle decimals and integers
    text = re.sub(r'(\d+)-year-old', r'\1-year-old', text)  # Handle "10-year-old" correctly
    text = text.replace("%", " percent")  # Replace % with "percent"
    return text

def num_to_words(number):
    """
    Convert a number to its word equivalent (fallback if num2words is not installed).
    """
    num_words = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
        "10": "ten",
        "11": "eleven",
        "12": "twelve",
        "13": "thirteen",
        "14": "fourteen",
        "15": "fifteen",
        "16": "sixteen",
        "17": "seventeen",
        "18": "eighteen",
        "19": "nineteen",
        "20": "twenty",
        "30": "thirty",
        "40": "forty",
        "50": "fifty",
        "60": "sixty",
        "70": "seventy",
        "80": "eighty",
        "90": "ninety"
    }
    
    if number in num_words:
        return num_words[number]
    
    if len(number) == 2:
        return f"{num_words[number[0] + '0']} {num_words[number[1]]}"
    
    return " ".join([num_words[digit] for digit in str(number)])

def add_speech_idiosyncrasies(text):
    """
    Add human-like speech patterns (pauses, stutters, filler words).
    """
    import random

    # List of filler words and pauses
    fillers = ["hmm", "uhh", "umm", "well", "you know", "like"]
    pauses = ["...", ",", "."]

    # Randomly insert fillers and pauses
    words = text.split()
    for i in range(len(words)):
        if random.random() < 0.1:  # 10% chance to add a filler
            words.insert(i, random.choice(fillers))
        if random.random() < 0.05:  # 5% chance to add a pause
            words.insert(i, random.choice(pauses))
    
    return " ".join(words)

def generate_podcast_script(params, research_data):
    length_details = determine_length_details(params["length"])
    current_date = datetime.now().strftime("%B %d, %Y")

    intro = f"Welcome to {params['podcast_name']}! I'm {params['speakers'][0]['name']} and today we're diving into {params['topic']}!"
    if params["num_speakers"] > 1:
        intro += " Joining me today are " + ", ".join([s["name"] for s in params["speakers"][1:]]) + "."
    
    system_prompt = textwrap.dedent(f"""
    You are a professional podcast script writer. Create a detailed, engaging, and natural-sounding podcast conversation about {params['topic']}.
    The podcast is titled "{params['podcast_name']}", but the focus of the discussion must be on {params['topic']}.
    Conduct deep research and include rare, granular facts and statistics in the speakers' responses.
    Use the following research data to inform the discussion and cite sources when necessary:
    
    {research_data}
    
    Follow these strict guidelines:
    
    1. Ensure {params['num_speakers']} speakers contribute equally throughout the discussion.
    2. Structure exactly {length_details['rebuttals']} rounds of rebuttals, where speakers actively engage and challenge each other’s points.
    3. The conversation must be structured so that each speaker takes turns contributing to every section, avoiding any speaker being omitted or underrepresented.
    4. Start with {params['speakers'][0]['name']} giving an AI disclaimer and introducing the topic.
    5. {params['speakers'][0]['name']} provides an insightful, data-backed summary of {params['topic']} before introducing the guests.
    6. Maintain a free-flowing discussion with varied tones, engagement styles, and interactive moments (interruptions, humor, and rhetorical questions where natural).
    7. Each speaker must reflect their assigned personality in their **vocabulary, sentence structure, and speaking rhythm** (e.g., an 'Expert' uses precise, technical language; a 'Storyteller' speaks in immersive, flowing narratives).
    8. Avoid robotic, scripted-sounding responses by ensuring natural-sounding phrasing, contractions, and dynamic interactions.
    9. Disagreements should take different forms, including:
         - **Factual disputes**: Challenge statistics or data interpretation.
         - **Value conflicts**: Differ on priorities or ethical considerations.
         - **Methodological critiques**: Question research approaches.
         - **Predictive disagreements**: Contrast future projections.
         - **Solution debates**: Propose competing approaches.
    10. Structure rebuttals to directly counter previous arguments rather than generic disagreements.
    11. Ensure citations are **naturally integrated into speech** (e.g., 'According to a 2023 study published in Nature...' rather than 'Source: [link]').
    12. Avoid repetitive or placeholder responses. Every reply must be **substantive, engaging, and factually grounded.**
    13. Ensure the conversation feels **like a real podcast, not a monologue or rigidly structured Q&A session.**
    14. Conclude with {params['speakers'][0]['name']} summarizing key takeaways and prompting listeners to subscribe.

    
    Speaker Details:
    """)

    for speaker in params["speakers"]:
        system_prompt += textwrap.dedent(f"""
        {speaker['name']} ({speaker['title']}): {speaker['description']}
        """)
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Generate a detailed podcast script for {params['podcast_name']} recorded on {current_date}. The focus of the discussion must be on {params['topic']}. Ensure the conversation lasts approximately {length_details['duration']} minutes and includes exactly {length_details['rebuttals']} rounds of rebuttals. Avoid repetition and placeholder text. Ensure meaningful engagement among speakers, and reflect their assigned personality in the way they speak. Include rare and granular facts and statistics in responses. Do not format speaker names in brackets or use 'Speaker 1'—use their assigned names naturally. Keep the conversation flowing without artificial separators or brackets between rounds. Ensure that all {params['num_speakers']} speakers take turns in a structured dialogue, with no one omitted."
            }
        ]
    )
    
    return response.content[0].text

def generate_speech(api_key, voice_id, text, output_file):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio file saved as {output_file}")
    else:
        print(f"Failed to generate audio: {response.status_code}")
        print(response.text)

def combine_audio_files(file_list, output_file):
    # Create a text file with the list of audio files
    with open("file_list.txt", "w") as f:
        for file in file_list:
            f.write(f"file '{file}'\n")
    
    # Use ffmpeg to concatenate the audio files
    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy", output_file
    ])
    print(f"Combined audio file saved as {output_file}")

def main():
    print("Welcome to Podcast Generator!\n")
    
    # Fetch available voices from Eleven Labs
    print("Fetching available voices...")
    voice_map = list_voices(ELEVEN_LABS_API_KEY)
    if not voice_map:
        print("No voices found. Exiting.")
        return

    # Get user input and assign voices
    params = get_user_input(voice_map)
    
    # Fetch research data
    print("\nFetching research data...")
    research_data = fetch_research_data(params["topic"])
    research_text = "\n".join([f"Source: {result['link']}\nSummary: {result['snippet']}" for result in research_data])
    
    print("\nGenerating podcast script...")
    script = generate_podcast_script(params, research_text)
    
    print("\n" + "="*50)
    print(f"{params['podcast_name'].upper()} PODCAST")
    print(f"Topic: {params['topic']}")
    print("="*50 + "\n")
    print(script)

    # Convert script to audio
    print("\nConverting script to audio...")
    audio_files = []
    line_counter = 1
    for line in script.split("\n"):
        if line.strip() == "":
            continue
        # Extract speaker name and text
        if ":" in line:
            speaker = line.split(":")[0].strip()
            text = ":".join(line.split(":")[1:]).strip()
            # Convert numbers and symbols to words
            text = convert_numbers_to_words(text)
            # Add human-like speech patterns
            text = add_speech_idiosyncrasies(text)
            # Find the voice ID for the speaker
            voice_id = None
            for participant in params["speakers"]:
                if normalized_speaker.upper() == participant["name"].upper():
                    voice_id = participant["voice_id"]
                    break
            if not voice_id:
                print(f"Voice for speaker '{speaker}' not found. Skipping line.")
                continue
            # Generate audio for the line
            output_file = f"{normalized_speaker}_line_{line_counter}.mp3"
            generate_speech(ELEVEN_LABS_API_KEY, voice_id, text, output_file)
            audio_files.append(output_file)
            line_counter += 1

    # Combine the audio files into a single podcast
    if audio_files:
        combine_audio_files(audio_files, "podcast.mp3")

    # Clean up temporary files
    for file in audio_files:
        os.remove(file)
    if os.path.exists("file_list.txt"):
        os.remove("file_list.txt")
    print("Temporary files removed.")

if __name__ == "__main__":
    main()