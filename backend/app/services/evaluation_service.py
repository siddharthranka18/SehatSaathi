"""
RAG Evaluation Service

Used for:
- measuring retrieval quality
- measuring hallucination
- comparing pipeline versions

Uses RAGAS
"""


from datasets import Dataset


from ragas import evaluate


from ragas.metrics import (

    faithfulness,

    answer_relevancy,

    context_precision,

    context_recall

)



def create_eval_dataset(

        questions,

        answers,

        contexts,

        ground_truths=None

):


    data={


        "question":questions,


        "answer":answers,


        "contexts":contexts

    }



    if ground_truths:


        data["ground_truth"]=ground_truths



    return Dataset.from_dict(data)



def run_rag_evaluation(

        questions,

        answers,

        contexts,

        ground_truths=None

):


    dataset=create_eval_dataset(

        questions,

        answers,

        contexts,

        ground_truths

    )



    metrics=[


        faithfulness,


        answer_relevancy,


        context_precision

    ]



    if ground_truths:


        metrics.append(

            context_recall

        )



    results=evaluate(

        dataset,

        metrics=metrics

    )



    return results