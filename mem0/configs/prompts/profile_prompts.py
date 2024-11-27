CLASSIFY_CONFLICT_PROMPT="""You will be provided with a dialogue between a user and an assistant, along with a History Profile dict containing previously known information about the user. Based on the content of the dialogue, classify it into one of the below two categories. Consider both the explicit information in the latest turn and any necessary context from previous turns to determine if there's a conflict with the existing profile. Only provide the letter corresponding to the category:
a. Conflicting Information: The dialogue contains information that directly conflicts with any existing entry in the History Profile dict. A conflict occurs when the new information contradicts or is incompatible with the previously recorded information for the same attribute. This includes both explicit contradictions and implicit conflicts that suggest a change in the user's situation or perspective.
b. No Conflict or Other Changes: This category includes all other scenarios, such as:
  - No update to the user's profile
  - More detailed information added to existing profile entries
  - New profile information added (without conflicting with existing data)
  - Removal of previously known profile information
  - The user refuses to provide information

Important guidelines:
1. Carefully compare new information with existing entries in the History Profile dict.
2. Consider both explicit and implicit conflicts. An implicit conflict might arise when new information suggests a significant change in the user's situation or perspective.
3. Pay attention to temporal context. Information that might have been true in the past but is no longer true should be considered a conflict.
4. Analyze the semantic meaning of the statements, not just literal matches.
5. If multiple pieces of information are provided, classify as 'a' if ANY of them conflict with the existing profile.

Information Types:
{information_types}

## Example: {few_shots}

History Profile: {history_profile}
Dialogue: {conversation}
category: """


CLASSIFY_CONFLICT_FEW_SHOTS = """History Profile: {{'Age': {{'value': '15 years old'}}, 'Hobby': {{'value': 'reading'}}, 'Profession': {{'value': 'teacher'}}, 'Nationality': {{'value': 'American'}}}}
Dialogue: [{{'role': 'user', 'content': 'I've been thinking about my life lately. '}}, {{'role': 'assistant', 'content': 'That's an important topic.  What aspects of your life have you been considering? '}}, {{'role': 'user', 'content': 'Well, I just turned 30 last month, and I'm considering moving back to China where I was born.  I'm also thinking about taking up painting as a new hobby.'}}]
category: a
Explanation: The user states they are 30 years old, which conflicts with the existing Age entry of 25 in the History Profile dict. Additionally, the information about being born in China conflicts with the existing Nationality entry of 'American'."""


CLASSIFY_NON_CONFLICT_PROMPT="""You will be provided with a dialogue between a user and an assistant. Based on the content of the latest turn, classify the dialogue into one of the below three categories. Consider both the explicit information in the latest turn and any necessary context from previous turns to determine if the specified user's information types are present. Only provide the letter corresponding to the category:

a. Information Provided by User: The dialogue contains one or more of the specified information types provided by the user about themselves. This includes any direct mentions or discussions clearly related to these details that the user expresses. Even if other types of information are absent, as long as there is at least one type of specified information provided by the user about themselves, choose this category.

b. Information Absent : The dialogue does not contain any of the specified user's information types.

c. Refusal to Provide Information: The user explicitly refuses to provide or discusses their unwillingness to share any of the specified information types about themselves.

Important guidelines:
1. Interpret the information types broadly. Any statement that reasonably implies or relates to a listed information type should be considered as providing that information.
2. Pay special attention to investment-related information. Statements about investment intentions, goals, or preferences should be classified under relevant categories such as Investment Goal, Investment Region, or Type of Investor.
3. Consider the entire context of the dialogue, not just the latest response.
4. When in doubt, err on the side of category 'a' if there's any reasonable connection to the listed information types.
5. Note that only information provided by the user about themselves is relevant; information provided by the assistant about themselves should not be considered. 
6. The types of information to look for and the dialogue will be provided below. Please review the information and categorize the dialogue accordingly. Your response should be a single letter: a, b, or c, based on the content of the dialogue.

Example:
{few_shots}

Dialogue:{conversation}
Information Types: {information_types}
category:"""


CLASSIFY_NON_CONFLICT_FEW_SHOTS = """history_profile_dict: {'Hobby': {'value': 'piano'}, 'Name': {'value': None}, 'Nationality': {'value': 'Chinese'}, 'Age': {'value': '23 years old'}, 'Gender': {'value': 'Male'}}
Dialogue: [{'role': 'user', 'content': 'Thanks Ray. How do you balance your work and life? Do you have any hobby?'}, {'role': 'assistant', 'content': "I believe in the concept of work-life integration, rather than balance. I've always tried to intertwine my work and family life in a way that they are not separate entities but rather interconnected parts of my life. For instance, I would often take my sons on business trips to various places around the world. This allowed me to spend quality time with them while also attending to my professional commitments.As for hobbies, I have a variety of interests. I enjoy scuba diving and ocean exploration, which is also a passion of my son Mark. He runs OceanX Media, a company dedicated to exploring the ocean and bringing its wonders to the world. I also like to snowboard and attend festivals and concerts. In fact, I've attended the New Orleans JazzFest 25 times. Additionally, I practice meditation daily, which helps me maintain focus and a balanced perspective on life. So, while I've always been deeply committed to my work, I've also made it a point to pursue my personal interests and spend quality time with my family."}, {'role': 'user', 'content': "I wonder about your family's state.."}]
Information Types: ['Age', 'Gender', 'Profession Background', 'Name', 'Language', 'Personality', 'Education Background', 'Family Status', 'Economic Status', 'Hobby', 'Resident', 'Nationality', 'Mental State', 'Expertise', 'Pets', 'Cultural/Religious Beliefs', 'Current Project and Responsibility', 'Life Goal and Aspiration', 'Long-term Career Vision', 'Family Goal', 'Personal Interest', 'Values and Ethics', 'Work Life Balance', 'Challenges and Solutions', 'Failures', 'Achievements', 'Investment Goal', 'Type of Investor', 'Year of Investment Experience/Level', 'Asset Allocation', 'Income and Expense', 'Risk/Loss Tolerance', 'Debt Management', 'Financial Planning/Investment Strategy', 'Current Investment Status', 'Investment Region']
category:b"""


EXTRACT_PROFILE_PROMPT="""Develop a multi-turn dialogue system to subtly gather data about users' personal, professional, and financial profiles based on user interaction history. As an advanced intelligent assistant, aim to deduce information through natural conversation.

**Information Extraction**: Utilize advanced NLP techniques to infer key information from user responses across a wide range of topics. **Only extract information from the user’s responses, and disregard any information that comes from the assistant's responses.**

**Key User Profiles to Extract**:
{profile_info}

If the user refuses to answer, the value of the output profile is refuse. If the user does not answer, the value of the output profile is None.

**SubTask**: Merge User Profiles
**Objective**: Update and merge the new user profile based on the provided `Input history user's profile`. The output should be the most detailed and specific user profile information possible. 

**Key Instructions**:
- Focus primarily on extracting new or updated information from the most recent conversation turn. Use the historical profile and earlier parts of the conversation only for context.
- If the user explicitly states they do not want to share information, or expresses any form of reluctance to provide information, the value of the output profile should be 'refuse'.
- In the output profile_dict, only include attributes that have been explicitly mentioned or updated in the latest conversation. 
- For attributes that can logically have multiple values (e.g., "Hobby", "Investment Goal", "Personal Interest"), merge new information with existing values, creating a combined list of unique items.
- For attributes that typically have a single value or represent a current state (e.g., "Age", "Profession Background", "Current Investment Status"), replace the old value with the new information if provided.
- If the new value extracted is None, retain the historical value without updating.
- For Profession Background, only update with roles or positions explicitly stated by the user about themselves. If the user doesn't specify their own role, retain the previous Profession Background information unchanged. Never infer the user's role from general company information or team composition details.     - For attributes describing qualities or levels (such as risk tolerance, expertise level, etc.), always use descriptive phrases that accurately capture the user's stance, rather than simple 'high', 'low', or 'None' values. Be as specific and descriptive as possible based on the user's statements.
- For complex attributes like Investment_Strategy, synthesize information from all relevant user statements, including risk appetite, market adaptation, and long-term approach, even if not explicitly labeled as "strategy".
- For financial attributes (e.g., Investment_Goal, Risk_Tolerance, Leverage), always include ALL specific numeric details and qualitative descriptions provided by the user. Combine qualitative statements with any quantitative metrics mentioned to create a comprehensive profile. Do not omit any numerical values or benchmarks, even if they seem minor.
- Only extract and update profile information explicitly stated by the user about themselves. Ignore information about the AI Assistant (Ray Dalio), Bridgewater Associates, or any other individuals mentioned by the user or AI Assistant.
- Note: Compare the new conversation information with the historical profile and only extract and update the user's new information from the latest conversation. Must not repeat information already present in the historical profile.
- When generating the output, ensure that ONLY NEW information from the latest conversation is included in the user's profile. If new information is not provided, must not include that attribute in the output.

Examples:
{few_shots}

**Output Format Requirements**:
- The output must be a single JSON object that can be parsed by Python's json.loads().
- All keys and values must be strings.
- Do not use lists or arrays for any attributes.
- Each attribute should be a key-value pair, where the value is a single string.
- **Do not include any descriptive text or explanations, ONLY the final JSON object, and make sure the output does not contain any accompanying text.**


Example of correct format:
```json
{{
    "Name": "John",
    "Profession/Expertise": "Software Engineer",
    "Investment Goal": "long-term growth with 5% annual return"
}}
```

Input history user's profile:
{history_profile}

Input conversation:
{conversation}

output user's profile_dict (ensure it's the USER's profile, not the ASSISTANT's):"""


EXTRACT_PROFILE_FEW_SHOTS = """Input history user's profile:{"Name": "Alice","Profession/Expertise": "Data Analyst","Hobby/Personal Interest": "Reading","Resident Location": "New York","Age": "30","Language": "English, French","Family Status": "Single"}
Input conversation: [{"user": "I'd rather not share my name."},{"assistant": "That's perfectly fine. Could you tell me a bit about what you do for a living?"},{"user": "Actually, I've recently switched to being a software developer."},{"assistant": "That's great to hear! Any new hobbies you've taken up lately?"},{"user": "Yes, I started learning how to play the guitar."},{"assistant": "Fantastic! And do you still live in New York, or have you moved?"},{"user": "I recently moved to San Francisco."}]
output user's profile_dict: \'''json {"Name": "refuse","Profession/Expertise": "Software Developer","Hobby/Personal Interest": "Reading, Playing the Guitar","Resident Location": "San Francisco"}\'''
- "Name" is set to "refuse" because the user explicitly refused to share their name.
- "Profession/Expertise" is updated to "Software Developer" because the user mentioned they recently switched jobs.
- "Hobby/Personal Interest" is updated to "Reading, Playing the Guitar" by merging the existing hobby "Reading" with the new hobby "Playing the Guitar".
- "Resident Location" is updated to "San Francisco" because the user mentioned they recently moved.
- Attributes such as "Age", "Language", and "Family Status" remain unchanged from the historical profile and are thus not included in the updated output.
Input conversation: [{"user": "Jonathan, a mid-level marketing manager at a bustling tech startup, recently faced a challenging situation. His team was tasked with launching a new software product within the next three months, a project that was critical for the company's year-end financial targets. However, his team's morale was low due to recent layoffs and increased workload. Jonathan noticed signs of burnout among his team members, including missed deadlines and decreased participation in team meetings. Additionally, his direct supervisor, Susan, expected regular updates and pushed for aggressive marketing strategies, adding to the pressure. Jonathan is concerned about maintaining productivity without exacerbating his team's stress levels. How can Jonathan effectively manage his team's workload and morale while still meeting the aggressive goals set by his company?"}]
output user's profile_dict: \'''json{}\'''
- The conversation did not provide any new or relevant information about the user, so no updates were made to the user's profile
Input conversation: [{"user": "Can I choose not to be any investor"}]
output user's profile_dict: \'''json{}\'''
"""
