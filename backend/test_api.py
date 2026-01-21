"""
Test script for Dental Interview Practice API
Demonstrates the complete interview flow
"""

import requests
import json
import time
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:8000"

def print_separator(title=""):
    """Print a visual separator"""
    print("\n" + "="*60)
    if title:
        print(f"  {title}")
        print("="*60)
    print()

def test_health_check():
    """Test the root endpoint"""
    print_separator("Testing Health Check")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_categories():
    """Test getting interview categories"""
    print_separator("Testing Get Categories")
    response = requests.get(f"{BASE_URL}/api/categories")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Total Categories: {data['total']}")
    print("Categories:")
    for i, category in enumerate(data['categories'], 1):
        print(f"  {i}. {category}")
    return response.status_code == 200

def test_get_interview_types():
    """Test getting interview types"""
    print_separator("Testing Get Interview Types")
    response = requests.get(f"{BASE_URL}/api/interview-types")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print("Available Interview Types:")
    for interview_type in data['types']:
        print(f"\n  Type: {interview_type}")
        print(f"  Description: {data['descriptions'][interview_type]}")
    return response.status_code == 200

def test_start_interview(interview_type="dentist"):
    """Test starting an interview"""
    print_separator(f"Testing Start Interview - {interview_type.title()}")
    
    payload = {
        "interview_type": interview_type,
        "user_name": "John Smith",
        "user_email": "john.smith@example.com"
    }
    
    print(f"Request Payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/interview/start",
        json=payload
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuestion Number: {data['question_number']}")
        print(f"Category: {data['category']}")
        print(f"Question:\n{data['question']}")
        return data
    else:
        print(f"Error: {response.json()}")
        return None

def test_generate_question(interview_type="dentist", question_number=2):
    """Test generating a follow-up question"""
    print_separator(f"Testing Generate Question #{question_number}")
    
    # Sample conversation history
    conversation_history = [
        {
            "role": "assistant",
            "content": "Hello John Smith! Thank you for taking the time to speak with us today. To start, could you tell me a bit about your background and what drew you to dentistry?"
        },
        {
            "role": "user",
            "content": "I graduated from dental school at UCLA in 2020. I was drawn to dentistry because I've always been passionate about combining artistic skills with healthcare. During my undergraduate years, I volunteered at a community health clinic where I saw firsthand the impact of oral health on overall wellbeing."
        }
    ]
    
    payload = {
        "interview_type": interview_type,
        "conversation_history": conversation_history,
        "question_number": question_number,
        "user_name": "John Smith"
    }
    
    print(f"Generating question for category: (will be determined by question number)")
    
    response = requests.post(
        f"{BASE_URL}/api/interview/question",
        json=payload
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuestion Number: {data['question_number']}")
        print(f"Category: {data['category']}")
        print(f"Question:\n{data['question']}")
        return data
    else:
        print(f"Error: {response.json()}")
        return None

def test_generate_audio(text="Hello! This is a test of the audio generation system."):
    """Test audio generation"""
    print_separator("Testing Audio Generation")
    
    print(f"Text to convert: '{text}'")
    
    response = requests.post(
        f"{BASE_URL}/api/audio/generate",
        params={"text": text}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        audio_length = len(data['audio_base64'])
        print(f"Audio generated successfully!")
        print(f"Base64 length: {audio_length} characters")
        print(f"Content type: {data['content_type']}")
        
        # Optionally save to file
        import base64
        audio_bytes = base64.b64decode(data['audio_base64'])
        with open('test_audio.mp3', 'wb') as f:
            f.write(audio_bytes)
        print("Audio saved to: test_audio.mp3")
        
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def test_complete_interview_flow(interview_type="dentist"):
    """Test a complete interview flow"""
    print_separator(f"Testing Complete Interview Flow - {interview_type.title()}")
    
    conversation_history = []
    
    # Start interview
    print("\n--- Question 1: Starting Interview ---")
    start_response = test_start_interview(interview_type)
    
    if not start_response:
        print("Failed to start interview")
        return False
    
    conversation_history.append({
        "role": "assistant",
        "content": start_response['question']
    })
    
    # Simulate user answers
    sample_answers = [
        "I graduated from dental school in 2020 and have been passionate about dentistry since childhood.",
        "I would carefully assess the patient's condition, explain all available options, and recommend the treatment that best balances clinical outcomes with the patient's preferences and financial situation.",
        "I believe in clear communication and always ensuring patients understand their treatment options. I make sure they feel comfortable asking questions and give them time to make informed decisions.",
        "I use digital tools to streamline workflows and maintain detailed records. I also believe in continuous improvement and regularly review our processes to identify efficiencies.",
        "I enjoy mentoring junior staff and helping them develop their skills. I'm also comfortable working independently when needed and can manage my own patient schedule effectively.",
        "I'm looking for a practice where I can grow professionally, contribute to a positive team culture, and make a meaningful impact on patient care. Work-life balance is also important to me.",
        "This interview has helped me reflect on my strengths and areas for growth. I'm genuinely excited about the opportunity to bring my skills to your practice and learn from the experienced team here."
    ]
    
    # Generate remaining questions
    for q_num in range(2, 8):
        print(f"\n--- Question {q_num} ---")
        
        # Add user's answer to history
        conversation_history.append({
            "role": "user",
            "content": sample_answers[q_num - 1]
        })
        
        # Generate next question
        payload = {
            "interview_type": interview_type,
            "conversation_history": conversation_history,
            "question_number": q_num,
            "user_name": "John Smith"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/interview/question",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Category: {data['category']}")
            print(f"Question: {data['question'][:150]}...")
            
            conversation_history.append({
                "role": "assistant",
                "content": data['question']
            })
            
            time.sleep(0.5)  # Small delay between requests
        else:
            print(f"Error: {response.json()}")
            return False
    
    print("\n✅ Complete interview flow successful!")
    print(f"Total exchanges: {len(conversation_history)}")
    return True

def main():
    """Run all tests"""
    print("\n" + "🏥"*30)
    print("  DENTAL INTERVIEW PRACTICE API - TEST SUITE")
    print("🏥"*30)
    
    tests = [
        ("Health Check", test_health_check),
        ("Get Categories", test_get_categories),
        ("Get Interview Types", test_get_interview_types),
        ("Start Interview (Dentist)", lambda: test_start_interview("dentist")),
        ("Start Interview (Hygienist)", lambda: test_start_interview("hygienist")),
        ("Generate Question #2", lambda: test_generate_question("dentist", 2)),
        ("Generate Question #5", lambda: test_generate_question("dentist", 5)),
        ("Generate Audio", test_generate_audio),
        ("Complete Interview Flow", lambda: test_complete_interview_flow("dentist")),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_separator("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    print("\n⚙️  Make sure the API server is running at http://localhost:8000")
    print("   Start it with: uvicorn main:app --reload\n")
    
    input("Press Enter to start tests...")
    main()
