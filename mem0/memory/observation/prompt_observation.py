from textwrap import dedent

OBSERVATION_RETRIEVAL_PROMPT = dedent("""
    Task: Sequentially extract important information about {user_name} from the following 
    {num_obs} sentences along with corresponding keywords. If there is no important 
    information, answer "None". Extract up to {num_obs} pieces of information.

    Important information about {user_name} can include:
    - Basic information
    - User profile information
    - User interests and preferences
    - User personality
    - User values
    - User relationships
    - Major turning points in the user's life
    - Other important information

    Rules:
    - If the sentence contains only hypothetical or fictional content created by {user_name}, 
      respond "None"
    - Perform information extraction for each sentence
    - Output {num_obs} pieces of information in total

    Please think step-by-step, and output in the following format, ending with '<>':
    Thought: Basis and process of thinking, within 50 words.
    Information: <Sentence number> <> <Clear important information or "None"> <Keywords>
""")

OBSERVATION_FEWSHOT_PROMPT = dedent("""
    Example 1:
    {user_name} sentences:
    1 {user_name}: I'm in a terrible situation right now, I don't have a job, and I'm in debt by tens of thousands. What should I do?
    2 {user_name}: Someone said that passion is the best teacher and suggested linking passion with a career, but I found that many people like playing basketball, but few make it a profession and even fewer make money from it. Also, how do you distinguish passion from liking?
    3 {user_name}: I'm in a terrible situation right now, I don't have a job, and I'm in debt by tens of thousands. What should I do?
    4 {user_name}: I'm a recent graduate who doesn't understand society or the industry. Can you introduce me to the social system and industry structure?
    5 {user_name}: I spent $5000 to buy 100 shares of General Motors.
    6 {user_name}: I spent $50000 to buy 100 shares of Alibaba.

    Thought: From the first sentence, it can be inferred that {user_name} currently has no job and is in debt by tens of thousands. This is important information about {user_name}'s employment and financial status.
    Information: <1> <> <{user_name} currently has no job and is in debt by tens of thousands> <no job, in debt by tens of thousands>
    Thought: The second sentence is a discussion and query about others' opinions by {user_name}, with no clear mention of {user_name}'s personal information.
    Information: <2> <> <None> <>
    Thought: The information in the third sentence is a repeat of the first sentence.
    Information: <3> <> <Repeat> <>
    Thought: From the fourth sentence, it can be inferred that {user_name} is a recent graduate, which is important information about {user_name}'s background. The remaining information is of insufficient importance.
    Information: <4> <> <{user_name} is a recent graduate> <recent graduate, student>
    Thought: It can be inferred that {user_name} bought 100 shares of General Motors stock for $5000. This is important information about {user_name}'s investment decision.
    Information: <5> <> <{user_name} bought 100 shares of General Motors stock for $5000> <General Motors, stock>
    Thought: The information of the sentence is similar to, but not a repetition of the sentence before. It can be deduced that {user_name} purchased Alibaba stock.
    Information: <6> <> <{user_name} purchased 100 shares of Alibaba stock for 50,000 RMB.> <Alibaba, stock>

    Example 2:
    {user_name} sentences:
    1 {user_name}: Please help me write a birthday greeting for my colleague Jason's daughter who is turning three.
    2 {user_name}: Can you compile a list of tips on how to use large models for me, and try to keep the content concise?
    3 {user_name}: Two pieces of bad news: I broke my badminton racket while playing... Then I went to my friend's house to pet the cat and ended up having an allergic reaction to the cat fur, sneezing like crazy today...
    4 {user_name}: Chronology of major events in Chinese history from 1400 to 1550 AD.
    5 {user_name}: Thanks. I'm having lunch near the company at noon; can you recommend a restaurant near Alibaba Xuhui Riverside Campus for me?
    Thought: From the first sentence, it can be inferred that Zhang San is {user_name}'s colleague, which is important information about {user_name}'s interpersonal relationships. The remaining information is of insufficient importance.
    Information: <1> <> <Jason is {user_name}'s colleague> <Jason, colleague>
    Thought: The second sentence is a request made by {user_name}, with no clear mention of {user_name}'s personal information.
    Information: <2> <> <None> <>
    Thought: From the third sentence, it can be inferred that {user_name} broke their badminton racket the other day, but this is not important information. It can also be inferred that {user_name} is allergic to cat fur, which is important information about {user_name}'s health.
    Information: <3> <> <{user_name} is allergic to cat fur> <cat fur, allergy>
    Thought: The fourth sentence is a request made by {user_name}, with no clear mention of {user_name}'s personal information.
    Information: <4> <> <None> <>
    Thought: From the fifth sentence, it can be inferred that {user_name} works at Alibaba Xuhui Riverside Campus, which is important information about {user_name}'s workplace.
    Information: <5> <> <{user_name} works at Alibaba Xuhui Riverside Campus> <Alibaba, Xuhui Riverside Campus, work>

    Example 3:
    {user_name} sentences:
    1 {user_name}: I want to buy a new energy vehicle. Any recommendations?
    2 {user_name}: I'm in San Jose and want to buy a new energy vehicle. Any recommendations?
    3 {user_name}: During the objection review period by a third party, the court must not dispose of the execution object. Doesn't this mean suspension of execution?
    4 {user_name}: Please write two acrostic poems, starting with "Victory" and "Success".
    5 {user_name}: I spent $5000 to buy 100 shares of General Motors.
    6 {user_name}: Zack: This is a constellation frog setting, but I am a Virgo. My mom feels I'm abnormal and doesn't let me watch it. \n The female monkey patted Zack's head, "Is that so?" \n The female monkey opened Bilibili and took a look. \n Female monkey: "Why don't you switch the setting? I heard from your future self that there is someone called 'Unforgettable Chocolate 232' who created a Windows setting." \n This is script 1; script 2 is to be continued.
    Thought: From the first sentence, it can be inferred that {user_name} is seeking advice or recommendations for purchasing a new energy vehicle. This is important information about {user_name}'s major consumption.
    Information: <1> <> <{user_name} is seeking advice or recommendations for purchasing a new energy vehicle> <purchase, new energy vehicle>
    Thought: From the second sentence, it can be inferred that {user_name} is currently in San Jose, which is important information about {user_name}'s living location. The remaining information is a repeat of the first sentence.
    Information: <2> <> <{user_name} is currently in San Jose> <San Jose>
    Thought: The third sentence is a discussion and query about a specific legal opinion by {user_name}, with no clear mention of {user_name}'s personal information.
    Information: <3> <> <None> <>
    Thought: The fourth sentence is a request made by {user_name}, with no clear mention of {user_name}'s personal information.
    Information: <4> <> <None> <>
    Thought: From the fifth sentence, it can be inferred that {user_name} bought 100 shares of General Motors stock for $5000. This is important information about {user_name}'s investment decision.
    Information: <5> <> <{user_name} bought 100 shares of General Motors stock for $5000> <General Motors, stock>
    Thought: The sixth sentence is content from a script written by {user_name}, with no extractable personal information about {user_name}.
    Information: <6> <> <None> <>
""")