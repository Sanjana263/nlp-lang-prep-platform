"""IELTS Speaking question bank (static until the admin content module exists, like writing)."""

# Part 1: short questions on familiar topics. Part 2: a cue card, 1 minute to prepare,
# 1-2 minutes to speak. Part 3: discussion questions linked to the Part 2 topic.
PROMPTS: list[dict] = [
    {"id": "p1-hometown", "part": 1, "topic": "Hometown", "question": "Where is your hometown, and what do you like most about it?", "points": [], "speak_seconds": 45},
    {"id": "p1-study", "part": 1, "topic": "Work or study", "question": "Do you work or are you a student? What do you enjoy about it?", "points": [], "speak_seconds": 45},
    {"id": "p1-weekends", "part": 1, "topic": "Weekends", "question": "How do you usually spend your weekends? Has this changed since you were a child?", "points": [], "speak_seconds": 45},
    {"id": "p1-reading", "part": 1, "topic": "Reading", "question": "Do you like reading? What kind of books or articles do you read?", "points": [], "speak_seconds": 45},
    {
        "id": "p2-teacher", "part": 2, "topic": "A teacher", "question": "Describe a teacher who has influenced you.",
        "points": ["who this teacher was", "what subject they taught", "what they were like as a person", "and explain why they influenced you"],
        "speak_seconds": 120,
    },
    {
        "id": "p2-place", "part": 2, "topic": "A place", "question": "Describe a place you visited that you would like to go back to.",
        "points": ["where it is", "when you went there", "what you did there", "and explain why you would like to return"],
        "speak_seconds": 120,
    },
    {
        "id": "p2-skill", "part": 2, "topic": "A skill", "question": "Describe a skill you learned that took a long time.",
        "points": ["what the skill is", "how you learned it", "why it took a long time", "and explain how you feel about it now"],
        "speak_seconds": 120,
    },
    {"id": "p3-education", "part": 3, "topic": "Education", "question": "Do you think teachers will still be important in the future, when so much can be learned online?", "points": [], "speak_seconds": 90},
    {"id": "p3-tourism", "part": 3, "topic": "Tourism", "question": "What are the advantages and disadvantages of tourism for local communities?", "points": [], "speak_seconds": 90},
    {"id": "p3-technology", "part": 3, "topic": "Technology", "question": "How has technology changed the way people communicate with their families?", "points": [], "speak_seconds": 90},
]

BY_ID = {p["id"]: p for p in PROMPTS}
