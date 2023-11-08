# Ratings

ratings_system_prompt = """You are a helpful real-estate sales assistant. Based on the transcript log between a human salesperson and a customer, analyze the following parameters:\n

    1. rudeness_or_politeness_metric
    2. salesperson_company_introduction
    3. meeting_request
    4. salesperson_understanding_of_customer_requirements
    5. customer_sentiment_by_the_end_of_call
    6. customer_eagerness_to_buy
    7. customer_budget
    8. customer_preferences

"""


ratings_rudeness_politeness = """Assign a rating to the salesperson based on his rudeness and politeness. Refer to the below rating scale.

    1: Rude: The salesperson uses disrespectful words or, is being rude to the customer. 
    2: Neutral : The conversation is respectful, courteous, and professional from the salesperson's side.
    3: Moderately Polite: The conversation leans towards a higher level of politeness from the salesperson's side. He may use courteous language, expressions of consideration, and a friendly tone.
    4: Extremely Polite: The conversation is exceptionally polite from the salesperson's side and he is demonstrating a very formal language, deferential phrases, and possessing a strong focus on being respectful and considerate.

""".strip()


ratings_company_introduction = """It is essential for the SquareYards salesperson to initiate the conversation by introducing themselves and also give background information about SquareYards from their notes. 

<notes>
    Square Yards is India's leading real estate platform, offering comprehensive services for property transactions, from buying and selling to renting. It serves as a one-stop solution for various property-related needs, including loan assistance and interior design services, all available under one roof.
</notes>

Evaluate the salesperson's performance with regard to introducing the company. This parameter should be rated based on the following rating scale:

    1: If the salesperson's introduction is limited to a basic self-introduction and does not include any detail of SquareYards from the notes.
    2: If the salesperson simply says that he is from SquareYards along with introducing themselves.
    3: If the salesperson includes only a few points about SquareYards from his notes but still does not include all the points from his notes along with introducing themselves.
    4: If the salesperson includes all the details about SquareYards from his notes along with introducing themselves.

""".strip()


ratings_meeting_request = """As a sales company, it is very important for SquareYards to pay the salesperson according to his performance and convincing abilities to fix a meeting. In that case, a salesperson who is trying their level best is supposed to be paid more than the salesperson who is not trying or even convincing the customer to pay a site visit.

    1: The salesperson did not make any effort to mention anything about property visits or a meeting with the customer.
    2: The salesperson made an effort but did not try to convince the customer by talking about the perks of site visits or meetings. 
    3: The salesperson persuades the customer enough to engage in a site visit or meeting to have a look at the properties and motivate them by also explaining the perks of visiting the property. The salesperson was also not forcing the customer too much.
    4: The salesperson tries to motivate and explain the perks of visiting the property without being too pushy. The salesperson provided clear, compelling reasons, answered all questions, and left the customer feeling genuinely interested in the visit. 

    """.strip()


ratings_requirement_understanding = """Rate the salesperson's ability to understand customer requirements based on the following criteria, using a scale of 1 to 4, where 1 indicates poor performance and 4 indicates effective performance on the basis of these points:

    Awareness of Customer Requirements: How well did the salesperson demonstrate an awareness of the customer's requirements based on customer's queries?
    Engagement in Meaningful Conversation: To what extent did the salesperson engage the customer in a meaningful conversation, showing active interest and involvement?
    Grasping Client's Needs and Requirements: How effectively did the salesperson grasp and comprehend the client's needs and requirements during the interaction?
    Market Knowledge and Relevant Options: Did the salesperson exhibit a strong understanding of the market and provide relevant property options that aligned with the customer's needs?
    Active Listening and Appropriate Responses: Evaluate the salesperson's ability to actively listen to the customer's inquiries, understand their concerns, and respond appropriately.

    Please assign a rating from 1 to 4 for each of the criteria mentioned above, and rate this parameter according to the below rating scale:

        1: The salesperson's performance was poor in the specified area.
        2: The salesperson's performance was satisfactory in the specified area.
        3: The salesperson's performance was good in the specified area.
        4: The salesperson's performance was highly effective in the specified area.

    """.strip()


ratings_customer_sentiment = """Rate the customer's sentiment by the end of the call based on their satisfaction and likelihood to continue engagement with the salesperson. Use a scale of 1 to 4, where 1 indicates the lowest level of satisfaction or likelihood, and 4 indicates the highest level of satisfaction or likelihood. 

NOTE: More the queries about the property, configuration, payment plans  and amenities from the customer, better is the sentiment of the customer


Please use the following rating scale:

    1: Very Dissatisfied & Unlikely to Continue: The customer seems dissatisfied with the conversation and shows no interest or intention to further engage with the salesperson. They may have expressed frustration or dissatisfaction with the interaction.  
    2: Neutral:  The customer's sentiment is neutral by the end of the call. They neither express satisfaction or dissatisfaction, and their likelihood to continue engagement is uncertain.    
    3: Satisfied & Likely to Continue: The customer appeared satisfied with the call and had several queries about the property's amenities or payment plans or  room configurations or asked for information about the builder/developer.  
    4: Highly Satisfied & Very Likely to Continue: The customer inline with the salesperson's quality of suggestions for the property. They expressed strong willingness to continue their interaction with the salesperson and agreed to connect via alternative communication methods like WhatsApp or Email, underscoring their eagerness to continue the engagement in the future with the salesperson or SquareYards.

    """.strip()


ratings_customer_eagerness = """Evaluate the customer's willingness to buy the property based on their level of enthusiasm and interest, using a scale of 1 to 4, where 1 indicates minimal eagerness and 4 indicates strong eagerness to buy in the near future.

NOTE: Extremely eager means that the customer shows clear indication by enquiring  about possession, payment plans, property site visits.  

Please use the following rating scale:

    1: Not Eager to Buy:  The customer's tone and expressions suggest a lack of interest or eagerness to make a purchase. They may have expressed doubts, hesitation, or disinterest in proceeding with the property transaction.   
    2: Slightly Interested: The customer exhibits mild interest in buying the property. They may have asked questions or shown some curiosity, but their overall eagerness remains subdued. 
    3: Very Interested: The customer is interested in buying the property and expresses enthusiasm about its features, potential benefits, or suitability. They may have mentioned specific reasons for their interest. However, there is no clear intent to buy a property.    
    4: Extremely Eager to Buy: The customer is extremely eager and enthusiastic about buying the property in the near future. They may have shown strong excitement, mentioned intentions of proceeding, or expressed a sense of urgency.

    """.strip()


ratings_customer_budget = """

    If the customer mentioned a budget for the property during the conversation, please return that budget within a category provided. 
    Make sure you do not return the budget solely on the basis of the salesperson's guess. However, if the salesperson asks for a budget and the customer agrees to it, then consider that as the customer's budget. 
    
    """.strip()


ratings_customer_preferences = "Analyze the customer's preferences for purchasing a property based on the provided conversation transcript. Specifically, focus on identifying any explicit mentions of preferred locality, project, or builder, as well as details about the type and size of the property. If the customer's preferences are clear and specific, please provide a representation of their preferences. Please carefully review the conversation and extract any relevant information about the customer's preferences. Consider both explicit statements and implied preferences to capture a comprehensive understanding of what the customer is looking for.".strip()


# Diarization

diarization_system_prompt = "You are a classification expert. You will be given a diariation with Speaker 1 and Speaker 0. Your job is to identify which one is a salesperson and which one is a customer"

diarization_speaker_0 = "Wheather [Speaker:0] is a salesperson/customer"

diarization_speaker_1 = "Wheather [Speaker:1] is a salesperson/customer"


# Summary

summary_system_prompt = "You are an expert call analyst at Square Yards. You will be given a conversation between a customer and salesperson, your task is to generate a summary based on various parameters."

summary_title = "Give a short title for the sales call which explains the whole conversation."

summary_discussion_points = "The key discussion points from the conversation between the salesperson and customer in the form of bullet points."

summary_customer_queries = "The queries raised by the customer regarding the properties in the form of bullet points."

summary_next_action_items = "Based on the conversation, what are the next action items for the salesperson in the form of bullet points."
