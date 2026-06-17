"""
Medical safety guardrails

Responsible:
- red flag detection
- emergency override
- unsafe output checking

Never allow LLM alone to decide emergency cases.
"""


import re


RED_FLAG_RULES = [


    {
        "name":"possible cardiac emergency",

        "keywords":[

            ["chest pain",
             "chest heaviness",
             "severe chest"],


            ["sweating",
             "breathlessness",
             "shortness of breath"]

        ],


        "message":

        "Your symptoms may require urgent medical attention. Please seek emergency care immediately."
    },



    {


        "name":"breathing emergency",


        "keywords":[

            [
            "difficulty breathing",
            "unable to breathe",
            "breathlessness"
            ]

        ],


        "message":

        "Breathing difficulty can be serious. Please seek urgent medical care."
    },



    {


        "name":"stroke symptoms",


        "keywords":[

            [
            "face drooping",
            "weakness one side",
            "speech problem",
            "confusion"
            ]

        ],


        "message":

        "These symptoms may require immediate emergency evaluation."

    },


    {

        "name":"loss of consciousness",

        "keywords":[

            [
            "unconscious",
            "fainted",
            "not responding"
            ]

        ],


        "message":

        "Loss of consciousness requires urgent medical evaluation."
    }

]



def normalize(text):

    return text.lower().strip()



def check_group(text, groups):

    """

    Each group means AND condition.

    Inside group means OR.


    Example:

    [
      ["chest pain","pressure"],

      ["sweating","breathing"]

    ]


    Means:

    chest pain OR pressure

    AND

    sweating OR breathing

    """


    for group in groups:


        found=False


        for word in group:


            if word in text:

                found=True
                break



        if not found:

            return False



    return True



def check_red_flags(
        patient_text:str
):


    text=normalize(patient_text)



    for rule in RED_FLAG_RULES:



        if check_group(

            text,

            rule["keywords"]

        ):


            return {


                "urgent":True,


                "reason":

                    rule["name"],



                "message":

                    rule["message"]

            }



    return {


        "urgent":False

    }



def validate_ai_response(
        answer:str
):

    """

    Prevent AI from making dangerous claims.

    """

    banned_patterns=[

        "you definitely have",

        "you are diagnosed with",

        "stop taking your medicine",

        "ignore doctor"

    ]


    text=answer.lower()



    for pattern in banned_patterns:


        if pattern in text:


            return {

                "safe":False,

                "reason":

                "Unsafe medical claim detected"

            }


    return {

        "safe":True

    }